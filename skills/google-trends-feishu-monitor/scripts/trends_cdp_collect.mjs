import { chromium } from 'playwright-core';

const DEFAULT_PORT = Number(process.env.TRENDS_CDP_PORT || 9225);
const DEFAULT_WAIT_MS = Number(process.env.TRENDS_WAIT_MS || 12000);
const DEFAULT_EXPLODING_THRESHOLD = Number(process.env.TRENDS_EXPLODING_THRESHOLD || 3000);

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function stripXssi(text) {
  return text.replace(/^\)\]\}',?\s*/, '');
}

function parseApiBody(text) {
  const cleaned = stripXssi(text);
  try {
    return JSON.parse(cleaned);
  } catch {
    return null;
  }
}

function parseJsonParam(url, key) {
  const value = new URL(url).searchParams.get(key);
  if (!value) {
    return null;
  }
  return JSON.parse(value);
}

function keywordFromRelatedUrl(url) {
  const req = parseJsonParam(url, 'req');
  return req?.restriction?.complexKeywordsRestriction?.keyword?.[0]?.value || '';
}

function averages(series) {
  if (!series.length) {
    return 0;
  }
  return series.reduce((sum, value) => sum + value, 0) / series.length;
}

function firstNonZeroIndex(series) {
  for (let i = 0; i < series.length; i += 1) {
    if (series[i] > 0) {
      return i;
    }
  }
  return -1;
}

function appearsNewInWindow(series) {
  const idx = firstNonZeroIndex(series);
  return idx > 0 && series.slice(0, idx).every((value) => value <= 0);
}

function meanAfterFirstNonZero(series) {
  const idx = firstNonZeroIndex(series);
  if (idx < 0) {
    return 0;
  }
  return averages(series.slice(idx));
}

function endsNearZero(series, threshold = 1) {
  if (!series.length) {
    return true;
  }
  const tail = series.slice(-2);
  return tail.every((value) => value <= threshold);
}

function isExplodingFormattedValue(value) {
  if (typeof value !== 'string') {
    return false;
  }
  const normalized = value.trim().toLowerCase();
  if (normalized === 'breakout' || value.trim() === '飙升') {
    return true;
  }
  const numeric = Number(normalized.replace(/[%+,]/g, ''));
  return Number.isFinite(numeric) && numeric > DEFAULT_EXPLODING_THRESHOLD;
}

async function withPage(fn) {
  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${DEFAULT_PORT}`);
  const context = browser.contexts()[0] || await browser.newContext();
  const page = await context.newPage();
  try {
    return await fn(page);
  } finally {
    await page.close().catch(() => {});
    await browser.close();
  }
}

async function collectResponses(page, targetUrl, waitMs) {
  const responses = [];
  const handler = async (response) => {
    const responseUrl = response.url();
    if (!responseUrl.includes('/trends/api/')) {
      return;
    }
    try {
      responses.push({
        url: responseUrl,
        status: response.status(),
        body: await response.text(),
      });
    } catch (error) {
      responses.push({
        url: responseUrl,
        status: response.status(),
        error: String(error),
      });
    }
  };

  page.on('response', handler);
  await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await sleep(waitMs);
  page.off('response', handler);
  const bodyText = await page.locator('body').innerText();
  return {
    title: await page.title(),
    url: page.url(),
    bodyText,
    responses,
  };
}

async function commandHealth(checkUrl) {
  return withPage(async (page) => {
    await page.goto('https://www.google.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await sleep(3000);
    const google = {
      title: await page.title(),
      url: page.url(),
      webdriver: await page.evaluate(() => navigator.webdriver),
    };
    const collected = await collectResponses(page, checkUrl, DEFAULT_WAIT_MS);
    const relatedStatuses = collected.responses
      .filter((item) => item.url.includes('/widgetdata/relatedsearches'))
      .map((item) => item.status);
    console.log(JSON.stringify({
      google,
      trends: {
        title: collected.title,
        url: collected.url,
        is429: /429|Too Many Requests/i.test(collected.bodyText),
        isSorry: /sorry/i.test(collected.url) || /sorry/i.test(collected.bodyText),
        relatedStatuses,
      },
    }, null, 2));
  });
}

async function commandRelated(targetUrl) {
  return withPage(async (page) => {
    const collected = await collectResponses(page, targetUrl, DEFAULT_WAIT_MS);
    const related = collected.responses
      .filter((item) => item.url.includes('/widgetdata/relatedsearches'))
      .map((item) => {
        const parsed = parseApiBody(item.body);
        const lists = parsed?.default?.rankedList || [];
        const rising = lists[1]?.rankedKeyword || [];
        return {
          rootKeyword: keywordFromRelatedUrl(item.url),
          status: item.status,
          parseable: Boolean(parsed),
          rising: rising.map((entry) => ({
            query: entry.query,
            formattedValue: entry.formattedValue,
            value: entry.value ?? null,
            isBreakout: ['breakout', '飙升'].includes(String(entry.formattedValue || '').trim().toLowerCase()) || String(entry.formattedValue || '').trim() === '飙升',
            qualifiesExploding: isExplodingFormattedValue(String(entry.formattedValue || '')),
          })),
        };
      });

    console.log(JSON.stringify({
      title: collected.title,
      url: collected.url,
      is429: /429|Too Many Requests/i.test(collected.bodyText),
      isSorry: /sorry/i.test(collected.url) || /sorry/i.test(collected.bodyText),
      related,
    }, null, 2));
  });
}

function buildCompareUrl(candidate, anchor, benchmark) {
  const q = `${anchor},${benchmark},${candidate}`;
  return `https://trends.google.com/trends/explore?date=now%207-d&q=${encodeURIComponent(q)}`;
}

async function commandCompare(candidate, anchor, benchmark) {
  return withPage(async (page) => {
    const compareUrl = buildCompareUrl(candidate, anchor, benchmark);
    const collected = await collectResponses(page, compareUrl, DEFAULT_WAIT_MS);
    const multiline = collected.responses.find((item) => item.url.includes('/widgetdata/multiline'));
    const parsed = multiline ? parseApiBody(multiline.body) : null;
    if (!multiline || multiline.status !== 200 || !parsed) {
      console.log(JSON.stringify({
        candidate,
        compareUrl,
        error: 'multiline_unavailable',
        is429: /429|Too Many Requests/i.test(collected.bodyText),
        isSorry: /sorry/i.test(collected.url) || /sorry/i.test(collected.bodyText),
        multilineStatus: multiline?.status || null,
      }, null, 2));
      return;
    }

    const timelineData = parsed.default?.timelineData || [];
    const rows = timelineData.map((item) => ({
      time: Number(item.time),
      formattedTime: item.formattedTime,
      values: item.value || [],
    }));
    const anchorSeries = rows.map((row) => Number(row.values[0] || 0));
    const benchmarkSeries = rows.map((row) => Number(row.values[1] || 0));
    const candidateSeries = rows.map((row) => Number(row.values[2] || 0));

    const candidateMean = meanAfterFirstNonZero(candidateSeries);
    const benchmarkMean = meanAfterFirstNonZero(benchmarkSeries);
    const ratio = benchmarkMean > 0 ? candidateMean / benchmarkMean : null;
    const qualifies = (
      appearsNewInWindow(candidateSeries) &&
      !endsNearZero(candidateSeries) &&
      ratio !== null &&
      ratio >= 0.8
    );

    console.log(JSON.stringify({
      candidate,
      anchor,
      benchmark,
      compareUrl,
      pointCount: rows.length,
      candidateFirstNonZeroIndex: firstNonZeroIndex(candidateSeries),
      benchmarkFirstNonZeroIndex: firstNonZeroIndex(benchmarkSeries),
      candidateIsNewInWindow: appearsNewInWindow(candidateSeries),
      candidateMeanAfterFirstNonZero: Number(candidateMean.toFixed(3)),
      benchmarkMeanAfterFirstNonZero: Number(benchmarkMean.toFixed(3)),
      candidateVsBenchmarkRatio: ratio === null ? null : Number(ratio.toFixed(3)),
      candidateEndsNearZero: endsNearZero(candidateSeries),
      qualifies,
      samplePoints: rows.slice(0, 6),
      tailPoints: rows.slice(-6),
    }, null, 2));
  });
}

const [command, ...args] = process.argv.slice(2);

if (command === 'health') {
  const url = args[0] || 'https://trends.google.com/trends/explore?date=now%207-d&q=seedance,wan,qwen,veo,sora';
  await commandHealth(url);
} else if (command === 'related') {
  const url = args[0];
  if (!url) {
    throw new Error('related requires a trends url');
  }
  await commandRelated(url);
} else if (command === 'compare') {
  const candidate = args[0];
  const anchor = args[1] || 'happy birthday images';
  const benchmark = args[2] || 'GPTs';
  if (!candidate) {
    throw new Error('compare requires a candidate keyword');
  }
  await commandCompare(candidate, anchor, benchmark);
} else {
  throw new Error('Usage: node scripts/trends_cdp_collect.mjs <health|related|compare> ...');
}
