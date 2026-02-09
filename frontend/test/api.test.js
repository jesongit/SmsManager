/**
 * SmsManager API 测试套件
 * 运行方式: npm run test:api
 */

import axios from 'axios';

const API = process.env.API_URL || 'http://localhost:8090';

let token = null;

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
  warn: (msg) => console.log(`  ${colors.yellow('⚠')} ${msg}`),
  section: (title) => {
    console.log(`\n${colors.bold(title)}`);
    console.log('─'.repeat(50));
  },
};

// 测试用例
const tests = {
  // 健康检查
  async testHealth() {
    this.section('健康检查');
    try {
      const res = await axios.get(`${API}/health`);
      log.pass('后端健康状态正常');
      return true;
    } catch (e) {
      log.fail(`后端不健康: ${e.message}`);
      return false;
    }
  },

  // 扫描测试
  async testScan() {
    this.section('设备扫描测试');
    try {
      const res = await axios.post(`${API}/api/devices/scan`);
      const { total_arp, total_scanned, local_ip } = res.data;

      log.info(`本机 IP: ${local_ip}`);
      log.info(`ARP 设备: ${total_arp}`);
      log.info(`扫描设备: ${total_scanned}`);

      if (local_ip) {
        log.pass('扫描功能正常');
        return true;
      }
      log.fail('未检测到本机 IP');
      return false;
    } catch (e) {
      log.fail(`扫描失败: ${e.message}`);
      return false;
    }
  },

  // 设备列表测试
  async testDeviceList() {
    this.section('设备列表测试');
    try {
      const res = await axios.get(`${API}/api/devices`);
      const { devices, total } = res.data;

      log.info(`设备总数: ${total}`);
      if (devices && Array.isArray(devices)) {
        log.pass(`获取到 ${devices.length} 个设备`);
        return true;
      }
      log.fail('返回数据格式错误');
      return false;
    } catch (e) {
      log.fail(`获取设备列表失败: ${e.message}`);
      return false;
    }
  },

  // 登录测试
  async testLogin() {
    this.section('登录测试');
    try {
      const res = await axios.post(`${API}/api/auth/login`, {
        username: 'admin',
        password: 'admin'
      });
      token = res.data.access_token;
      log.pass('登录成功');
      log.info(`Token: ${token.substring(0, 30)}...`);
      return true;
    } catch (e) {
      if (e.response?.status === 422) {
        log.warn('需要 TOTP 验证码（项目已启用 2FA）');
        log.info('跳过登录测试');
        return true;
      }
      log.fail(`登录失败: ${e.message}`);
      return false;
    }
  },

  // 认证测试
  async testAuth() {
    if (!token) {
      this.section('认证测试');
      log.warn('无 Token，跳过认证测试');
      return true;
    }

    this.section('认证测试');
    try {
      const res = await axios.get(`${API}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      log.info(`用户: ${res.data.username}`);
      log.pass('认证成功');
      return true;
    } catch (e) {
      log.fail(`认证失败: ${e.message}`);
      return false;
    }
  },

  // 辅助方法
  section(title) {
    console.log(`\n${colors.bold(title)}`);
    console.log('─'.repeat(50));
  }
};

// 主测试函数
async function runTests() {
  const startTime = Date.now();

  console.log(colors.bold('\n🧪 SmsManager API 测试套件'));
  console.log(`   API: ${API}`);
  console.log(`   时间: ${new Date().toLocaleString()}`);

  const results = [];

  // 运行所有测试
  results.push(await tests.testHealth());
  results.push(await tests.testScan());
  results.push(await tests.testDeviceList());
  results.push(await tests.testLogin());
  results.push(await tests.testAuth());

  // 统计结果
  const passed = results.filter(r => r).length;
  const failed = results.filter(r => !r).length;
  const time = ((Date.now() - startTime) / 1000).toFixed(2);

  console.log('\n' + '='.repeat(50));
  console.log(colors.bold('📊 测试结果'));
  console.log(`   ${colors.green('通过')}: ${passed}`);
  console.log(`   ${colors.red('失败')}: ${failed}`);
  console.log(`   用时: ${time}s`);

  if (failed === 0) {
    console.log(`\n${colors.green('🎉 所有测试通过!')}\n`);
    process.exit(0);
  } else {
    console.log(`\n${colors.red('❌ 部分测试失败')}\n`);
    process.exit(1);
  }
}

// 运行
runTests().catch(e => {
  console.error(colors.red('\n💥 测试崩溃:'), e.message);
  process.exit(1);
});
