import {fileURLToPath} from 'node:url';
import test from 'ava';
import {execaNode} from 'execa';
import {Chalk} from '../source/index.js';

const fixture = fileURLToPath(new URL('_fixture.js', import.meta.url));

// `COLORTERM`/`TERM` are set so that environment detection would report
// truecolor support if `FORCE_COLOR` did not override it.
const runFixture = forceColor => execaNode(fixture, {
	extend: false,
	env: {
		COLORTERM: 'truecolor',
		TERM: 'xterm-256color',
		...(forceColor !== undefined && {FORCE_COLOR: forceColor}),
	},
});

const expectedOutput = level => {
	const chalk = new Chalk({level});
	return `${chalk.hex('#ff6159')('testout')} ${chalk.hex('#ff6159')('testerr')}`;
};

test('FORCE_COLOR=0 disables colors', async t => {
	const {stdout} = await runFixture('0');
	t.is(stdout, expectedOutput(0));
});

test('FORCE_COLOR=1 forces exactly basic colors', async t => {
	const {stdout} = await runFixture('1');
	t.is(stdout, expectedOutput(1));
});

test('FORCE_COLOR=2 forces exactly 256 colors', async t => {
	const {stdout} = await runFixture('2');
	t.is(stdout, expectedOutput(2));
});

test('FORCE_COLOR=3 forces exactly 16m colors', async t => {
	const {stdout} = await runFixture('3');
	t.is(stdout, expectedOutput(3));
});

test('FORCE_COLOR levels produce distinct output', t => {
	t.not(expectedOutput(1), expectedOutput(2));
	t.not(expectedOutput(2), expectedOutput(3));
});

test('out-of-range FORCE_COLOR is treated as not set', async t => {
	const {stdout: baseline} = await runFixture(undefined);

	for (const forceColor of ['-1', '4', 'abc']) {
		// eslint-disable-next-line no-await-in-loop
		const {stdout} = await runFixture(forceColor);
		t.is(stdout, baseline, `FORCE_COLOR=${forceColor}`);
	}
});

test('FORCE_COLOR=true acts as a minimum level of 1', async t => {
	const {stdout} = await runFixture('true');
	t.is(stdout, expectedOutput(3));
});

test('empty FORCE_COLOR acts as a minimum level of 1', async t => {
	const {stdout} = await runFixture('');
	t.is(stdout, expectedOutput(3));
});
