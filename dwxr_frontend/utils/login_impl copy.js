/*
 * @Author: Dong-dz 505403623@qq.com
 * @Date: 2025-07-14 20:59:50
 * @LastEditors: Dong-dz 505403623@qq.com
 * @LastEditTime: 2025-08-10 16:23:25
 * @FilePath: \打窝仙人\utils\login_impl.js
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import { request } from './promisify_impl';

// 是否登录开发者服务端
let isDeveloperServerLogin = false;
// 是否登录抖音主端
let isDouyinLogin = false;
let loginData = null;

class LoginController {

  _token = '';
  _openid = '';
  _unionid = '';
  _username = '';

  /**
   * @description: 登录函数，首先调用tt.login获取openid，并向开发者服务端请求登录
   * @param {boolean} force 当用户未登录抖音app时，是否强制调起抖音app登录界面
   * @return {boolean}
   */
  async login (force = true) {
    const openid = 'adminUser1';
    console.log('[login] 检查用户是否登录, isDeveloperServerLogin:', isDeveloperServerLogin, 'isDouyinLogin:', isDouyinLogin, 'force:', force);
    if (isDeveloperServerLogin) {
      console.log('[login] 已登录开发者服务端，直接返回');
      return;
    }
    try {
      console.log('[login] 调用 登录接口');
      await this.loginToDeveloperServer(openid);
      console.log('[login] 登录接口返回loginToDeveloperServer', isDeveloperServerLogin);
    } catch (err) {
      console.log('[login] 登录接口返回loginToDeveloperServer error:', err, 'loginData:', loginData, 'isDouyinLogin:', isDouyinLogin);
      tt.showToast({
        title: '[login] 授权登录失败',
        icon: 'fail',
      });
    }
    return isDeveloperServerLogin;
  }

  /**
   * @description: 请求服务端，
   * @param {string} openid tt.login返回的openid
   * @return {*}
   */
  async loginToDeveloperServer (openid) {
    try {
      console.log('[loginToDeveloperServer] 调用后端登录接口', openid);
      const res = await request({
        url: `/users/${openid}`,
        method: 'get'
      });
      // 结果判断
      if (res.statusCode == 200) {
        console.log('[loginToDeveloperServer] 调用后端获取用户信息成功:', res, res.data.openid, res.data.name);
        this._openid = res.data.openid;
        this._username = res.data.name;
        isDeveloperServerLogin = true;
        isDouyinLogin = true;
      } else {
        console.warn('[loginToDeveloperServer] 调用后端未获取到用户信息');
      }
    }
    catch (err) {
      console.log('[loginToDeveloperServer] 调用登录接口失败:', err);
    }

  }

  /**
   * @description: 登出开发者服务端
   * @return {*}
   */
  async logout () {
    console.log('[logout] start');
    await request({
      url: '/api/apps/logout',
      method: 'post',
      data: {
        token: loginController.getToken(),
      },
    });
    isDeveloperServerLogin = false;
    tt.removeStorageSync('token');
    tt.removeStorageSync('openid');
    tt.removeStorageSync('unionid');
    tt.removeStorageSync('phoneNumberLogin');
    tt.removeStorageSync('customLogin');
    console.log('[logout] end, 已清除本地存储');
  }

  /**
   * @description: 获取localStorage中的token
   * @return {string}
   */
  getToken () {
    const token = this._token || tt.getStorageSync('token');
    console.log('[getToken] 返回 token:', token);
    return token;
  }

  /**
   * @description: 返回是否登录抖音主端
   * @return {*}
   */
  isDouyinLogin () {
    console.log('[isDouyinLogin] 返回 isDouyinLogin:', isDouyinLogin);
    return isDouyinLogin;
  }

  /**
   * @description: 是否登录开发者服务端
   * @return {*}
   */
  isDeveloperServerLogin () {
    console.log('[isDeveloperServerLogin] 返回 isDeveloperServerLogin:', isDeveloperServerLogin);
    return isDeveloperServerLogin;
  }

  // openid和unionid由开发者服务端下发，此处只是为了前端做展示；
  // 在实际情况中不建议开发者下发openid和unionid
  /**
   * @description: 获取localStorage中的openid
   * @return {string}
   */
  getOpenid () {
    const openid = this._openid || tt.getStorageSync('openid');
    console.log('[getOpenid] 返回 openid:', openid);
    return openid;
  }
  getUsername () {
    const username = this._username //|| tt.getStorageSync('openid');
    console.log('[getUsername] 返回 username:', username);
    return username;
  }

  /**
   * @description: 获取localStorage中的unionid
   * @return {string}
   */
  getUnionid () {
    const unionid = this._unionid || tt.getStorageSync('unionid');
    console.log('[getUnionid] 返回 unionid:', unionid);
    return unionid;
  }
}
export const loginController = new LoginController();
