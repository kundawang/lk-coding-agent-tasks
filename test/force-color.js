import {fileURLToPath} from 'node:url';
import test from 'ava';
import {execaNode} from 'execa';

const fixture = fileURLToPath(new URL('_fixture-force-color.js', import.meta.url));

// `COLORTERM=truecolor` makes environment detection report level 3,
// so tests can tell exact FORCE_COLOR levels apart from detection results.
const runFixture = async forceColor => {
	const env = {COLORTERM: 'truecolor'};
	if (forceColor !== undefined) {
		env.FORCE_COLOR = forceColor;
	}

	const {stdout} = await execaNode(fixture, {env, extend: false});
	const [levelLine, output] = stdout.split('\n');
	return [levelLine.replace('level=', ''), output];
};

test('FORCE_COLOR=0 disables colors', async t => {
	const [level, output] = await runFixture('0');
	t.is(level, '0');
	t.is(output, 'test');
});

test('FORCE_COLOR=1 forces exactly basic colors', async t => {
	const [level, output] = await runFixture('1');
	t.is(level, '1');
	t.true(output.startsWith('\u{1B}['));
});

test('FORCE_COLOR=2 forces exactly 256 colors', async t => {
	const [level, output] = await runFixture('2');
	t.is(level, '2');
	t.is(output, '\u{1B}[38;5;210mtest\u{1B}[39m');
});

test('FORCE_COLOR=3 forces exactly truecolor', async t => {
	const [level, output] = await runFixture('3');
	t.is(level, '3');
	t.is(output, '\u{1B}[38;2;255;97;89mtest\u{1B}[39m');
});

test('FORCE_COLOR=2 and FORCE_COLOR=3 produce different output', async t => {
	const [, output2] = await runFixture('2');
	const [, output3] = await runFixture('3');
	t.not(output2, output3);
});

test('FORCE_COLOR above 3 is treated as not set', async t => {
	const [level] = await runFixture('4');
	t.is(level, '3');
});

test('negative FORCE_COLOR is treated as not set', async t => {
	const [level] = await runFixture('-1');
	t.is(level, '3');
});

test('non-numeric FORCE_COLOR is treated as not set', async t => {
	const [level] = await runFixture('abc');
	t.is(level, '3');
});

test('empty FORCE_COLOR still enables basic colors', async t => {
	const [level] = await runFixture('');
	t.is(level, '3');
});

test('FORCE_COLOR=true still enables basic colors', async t => {
	const [level] = await runFixture('true');
	t.is(level, '3');
});

test('FORCE_COLOR=false still disables colors', async t => {
	const [level, output] = await runFixture('false');
	t.is(level, '0');
	t.is(output, 'test');
});

test('environment detection is used when FORCE_COLOR is not set', async t => {
	const [level] = await runFixture(undefined);
	t.is(level, '3');
});
