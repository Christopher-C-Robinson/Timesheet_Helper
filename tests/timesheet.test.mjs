// Runs the timesheet logic exactly as the GitHub Pages site serves it
// (docs/index.html), so these tests cover the live code path.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const fixture = (name) => fs.readFileSync(path.join(here, 'fixtures', name), 'utf8');

function loadSiteLogic(htmlPath) {
    const html = fs.readFileSync(htmlPath, 'utf8');
    const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
    const marker = '// ── UI helpers ──';
    assert.ok(script.includes(marker), 'UI helpers marker missing from page script');
    const core = script.split(marker)[0];
    const ctx = {};
    vm.createContext(ctx);
    vm.runInContext(
        core + '\nthis.api = { removeTimespans, replaceWithDuration, splitTaskLine };',
        ctx
    );
    return ctx.api;
}

const site = loadSiteLogic(path.join(root, 'docs', 'index.html'));
const input = fixture('sample-week.txt');

test('docs/index.html and templates/static_index.html stay identical', () => {
    assert.equal(
        fs.readFileSync(path.join(root, 'docs', 'index.html'), 'utf8'),
        fs.readFileSync(path.join(root, 'templates', 'static_index.html'), 'utf8')
    );
});

test('duration output matches the expected sample week exactly', () => {
    const actual = site.replaceWithDuration(input).replace(/\n+$/, '');
    const expected = fixture('sample-week.expected-duration.txt').replace(/\n+$/, '');
    assert.equal(actual, expected);
});

test('email output matches the expected sample week exactly', () => {
    const actual = site.removeTimespans(input).replace(/\n+$/, '');
    const expected = fixture('sample-week.expected-email.txt').replace(/\n+$/, '');
    assert.equal(actual, expected);
});

test('no leftover separators before the hours', () => {
    for (const line of site.replaceWithDuration(input).split('\n')) {
        assert.ok(!line.includes(' ,'), `stray " ," in ${JSON.stringify(line)}`);
        assert.ok(!/[,;]\s*[\d.]+$/.test(line), `dangling separator in ${JSON.stringify(line)}`);
    }
});

test('day and weekly totals are unchanged', () => {
    const out = site.replaceWithDuration(input);
    const totals = Object.fromEntries(
        [...out.matchAll(/^(\w+day) Total: ([\d.]+) hours$/gm)].map((m) => [m[1], m[2]])
    );
    assert.deepEqual(totals, {
        Monday: '11.00',
        Tuesday: '11.50',
        Wednesday: '12.25',
        Thursday: '12.75',
        Friday: '6.75',
    });
    assert.match(out, /Weekly Total: 54\.25 hours$/);
});

test('multi-range lines from the bug report', () => {
    const out = site.replaceWithDuration(input).split('\n');
    for (const line of [
        '• QA Feature 37871: Android Application 3rd Party Data Background Sync 6.25',
        '• QA Feature 38488: Forms Pro Application Interface Updates 2026 3.75',
        '• QA Feature 37871: Android Application 3rd Party Data Background Sync 5.25',
        '• QA Feature 37871: Android Application 3rd Party Data Background Sync 1.50',
        '• QA Feature 38488: Forms Pro Application Interface Updates 2026 7.75',
    ]) {
        assert.ok(out.includes(line), `missing ${JSON.stringify(line)}`);
    }
});

test('title commas, colons, and number ranges are kept', () => {
    const cases = [
        ['Test fixes from Next run 145058: versioning, theme colors, GET failure, and static table color 4:15-4:45',
            'Test fixes from Next run 145058: versioning, theme colors, GET failure, and static table color'],
        ['QA: List-page automated tests 39305-39309 11-11:30', 'QA: List-page automated tests 39305-39309'],
        ['E2E (38641, 38642) 2:45-4:15', 'E2E (38641, 38642)'],
        ['release 2610.0.0 branch sync 11:15-11:30', 'release 2610.0.0 branch sync'],
    ];
    for (const [line, title] of cases) {
        assert.equal(site.splitTaskLine(line).title, title);
    }
});

for (const ranges of [
    '8-9, 10-11, 1-2',
    '8-9,10-11,1-2',
    '8-9 , 10-11 , 1-2',
    '8-9; 10-11; 1-2',
    '8-9, 10-11 and 1-2',
    '8-9, 10-11, and 1-2',
    '8-9 & 10-11 & 1-2',
    '8-9.  10-11.  1-2',
    '8-9,   10-11,1-2,  ',
]) {
    test(`separator variant ${JSON.stringify(ranges)}`, () => {
        const title = 'QA: Admin API (38641, 38642) tests 39305-39309';
        const out = site.replaceWithDuration(`•\tMonday\no\t${title} ${ranges}\n`);
        assert.ok(out.split('\n').includes(`• ${title} 3.00`), out);
        const email = site.removeTimespans(`•\tMonday\no\t${title} ${ranges}\n`);
        assert.ok(email.split('\n').includes(`\t• ${title}`), email);
    });
}
