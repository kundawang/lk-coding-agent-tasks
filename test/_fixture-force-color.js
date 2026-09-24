import {createSupportsColor} from '../source/vendor/supports-color/index.js';
import chalk from '../source/index.js';

const result = createSupportsColor({isTTY: true});
console.log(`level=${result ? result.level : 0}`);
console.log(chalk.hex('#ff6159')('test'));
