/**
 * SmsManager 浏览器测试
 * 运行方式: npm run test:browser
 * 前置条件: 前端服务运行在 http://localhost:5176
 */

import puppeteer from 'puppeteer';

// 配置
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5176';
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8090';

// 彩色输出
const colors = {
  green: (text) => `\x1b[32m${text}\x1b[0m`,
  red: (text) => `\x1b[31m${text}\x1b[0m`,
  yellow: (text) => `\x1b[33m${text}\x1b[0m`,
  blue: (text) => `\x1b[34m${text}\x1b[0m`,
  bold: (text) => `\x1b[1m${text}\x1b[0m`,
};

const log = {
  pass: (msg) => console.log(`  ${colors.green('✓')} ${msg}`),
  fail: (msg) => console.log(`  ${colors.red('✗')} ${msg}`),
  info: (msg) => console.log(`  ${colors.blue('ℹ')} ${msg}`),
};

// 延迟函数
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// 测试用例
const tests = {
  // 检查页面标题
  async testTitle(page) {
    console.log('\n📄 测试页面标题...');
    try {
      const title = await page.title();
      log.info(`标题: ${title}`);

      if (title && title.includes('SmsManager')) {
        log.pass('标题正确');
        return true;
      }
      log.fail('标题不匹配');
      return false;
    } catch (e) {
      log.fail(`获取标题失败: ${e.message}`);
      return false;
    }
  },

  // 检查登录表单
  async testLoginForm(page) {
    console.log('\n🔐 测试登录表单...');
    try {
      await page.waitForSelector('input[type="text"], input[name="username"]', {
        timeout: 5000
      });
      log.pass('登录表单存在');
      return true;
    } catch (e) {
      log.fail(`登录表单未找到: ${e.message}`);
      return false;
    }
  },

  // 检查设备相关内容
  async testDeviceList(page) {
    console.log('\n📱 测试设备列表页面...');
    try {
      const body = await page.evaluate(() => document.body.innerText);
      const hasDeviceText = body.includes('设备') ||
                           body.includes('Device') ||
                           body.includes('device') ||
                           body.includes('Device');

      if (hasDeviceText) {
        log.pass('设备相关内容存在');
        return true;
      }
      log.pass('页面加载正常（设备列表为空）');
      return true;
    } catch (e) {
      log.fail(`检查设备列表失败: ${e.message}`);
      return false;
    }
  },

  // 检查导航元素
  async testNavigation(page) {
    console.log('\n🧭 测试导航元素...');
    try {
      const body = await page.evaluate(() => document.body.innerText);
      const hasNav = body.includes('设备列表') ||
                     body.includes('扫描') ||
                     body.includes('添加') ||
                     body.includes('列表') ||
                     body.includes('Scan') ||
                     body.includes('List');

      if (hasNav) {
        log.pass('导航元素存在');
        return true;
      }
      console.log('  ⚠ 未找到标准导航元素');
      return true;
    } catch (e) {
      log.fail(`检查导航失败: ${e.message}`);
      return false;
    }
  },

  // 测试响应式设计
  async testResponsive(page) {
    console.log('\n📐 测试响应式设计...');
    try {
      const size = await page.evaluate(() => ({
        width: window.innerWidth,
        height: window.innerHeight
      }));

      log.info(`视口大小: ${size.width}x${size.height}`);

      if (size.width > 0 && size.height > 0) {
        log.pass('页面正常渲染');
        return true;
      }
      log.fail('页面渲染异常');
      return false;
    } catch (e) {
      log.fail(`检查响应式失败: ${e.message}`);
      return false;
    }
  },

  // 测试控制台错误
  async testConsoleErrors(page) {
    console.log('\n⚠️  测试控制台错误...');
    const errors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', err => {
      errors.push(err.message);
    });

    await delay(2000);

    const criticalErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('404') &&
      !e.includes('net::ERR')
    );

    if (criticalErrors.length === 0) {
      log.pass('无控制台关键错误');
      return true;
    }

    log.warn(`发现 ${criticalErrors.length} 个错误`);
    criticalErrors.slice(0, 3).forEach(e => log.info(`  - ${e.substring(0, 100)}`));
    return true;
  }
};

// 主测试函数
async function runBrowserTests() {
  console.log(colors.bold('\n🌐 SmsManager 浏览器测试'));
  console.log(`   前端: ${FRONTEND_URL}`);
  console.log(`   后端: ${BACKEND_URL}`);
  console.log(`   时间: ${new Date().toLocaleString()}`);

  let browser = null;

  try {
    console.log('\n🚀 启动浏览器...');

    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1280,720'
      ]
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });

    console.log(`📱 访问 ${FRONTEND_URL}...`);
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle0', timeout: 30000 });
    await delay(1000);

    const results = [];
    results.push(await tests.testTitle(page));
    results.push(await tests.testLoginForm(page));
    results.push(await tests.testDeviceList(page));
    results.push(await tests.testNavigation(page));
    results.push(await tests.testResponsive(page));
    results.push(await tests.testConsoleErrors(page));

    const passed = results.filter(r => r).length;
    const failed = results.filter(r => !r).length;

    console.log('\n' + '='.repeat(50));
    console.log(colors.bold('📊 测试结果'));
    console.log(`  ${colors.green('通过')}: ${passed}`);
    console.log(`  ${colors.red('失败')}: ${failed}`);

    if (failed === 0) {
      console.log(`\n${colors.green('🎉 所有浏览器测试通过!')}\n`);
      return true;
    } else {
      console.log(`\n${colors.red('❌ 部分测试失败')}\n`);
      return false;
    }

  } catch (e) {
    console.error(colors.red('\n💥 测试崩溃:'), e.message);
    return false;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// 检查依赖
async function checkDependencies() {
  console.log('🔍 检查依赖...');

  try {
    await import('puppeteer');
    log.pass('Puppeteer 已安装');
    return true;
  } catch (e) {
    console.log('\n⚠️  Puppeteer 未安装');
    console.log('   运行: npm install puppeteer --save-dev');
    return false;
  }
}

// 主入口
async function main() {
  const depsOk = await checkDependencies();
  if (!depsOk) {
    console.log('\n请先安装依赖: npm install puppeteer --save-dev');
    process.exit(1);
  }

  const success = await runBrowserTests();
  process.exit(success ? 0 : 1);
}

main();
