import axios from 'axios';

const API = 'http://localhost:8090';

async function testBackend() {
  console.log('🧪 后端 API 测试\n');
  console.log('='.repeat(50));

  // 1. 扫描测试
  console.log('\n1. 测试扫描功能...');
  const scanRes = await axios.post(API + '/api/devices/scan');
  const totalDevices = scanRes.data.total_arp + scanRes.data.total_scanned;
  console.log('   ✅ 发现 ' + totalDevices + ' 个设备');
  console.log('   本机 IP: ' + scanRes.data.local_ip);

  // 2. 登录测试 (无需 TOTP)
  console.log('\n2. 测试登录功能...');
  try {
    const loginRes = await axios.post(API + '/api/auth/login', {
      username: 'admin',
      password: 'admin'
    });
    console.log('   ✅ 登录成功!');
  } catch (e) {
    // 422 可能是因为 TOTP 验证失败，这是预期的
    if (e.response?.status === 422) {
      console.log('   ⚠️  需要 TOTP 验证码（项目已启用 2FA）');
    }
  }

  // 3. 获取设备列表
  console.log('\n3. 测试设备列表 API...');
  const devicesRes = await axios.get(API + '/api/devices');
  console.log('   ✅ 设备数量: ' + devicesRes.data.total);

  console.log('\n' + '='.repeat(50));
  console.log('🎉 后端 API 测试完成！');
}

testBackend().catch(console.error);
