import { request } from './promisify_impl';


class biandian {
  async bd_list (code) {
    console.log('[bd_list] start');
    const res = {};
    try {
      console.log('[bd_list] 调用标点查询接口');
      res = await request({
        url: `/biaodian/${code}`,
        method: 'get'
      });
      // 结果判断
      if (res.statusCode == 200) {
        console.log('[bd_list] 调用后端获取标点成功:', res);
        // this._openid = res.data.openid;
        // this._username = res.data.name;
        // isDeveloperServerLogin = true;
        // isDouyinLogin = true;
      } else {
        console.warn('[bd_list] 调用后端未获取到标点信息');
      }
    }
    catch (err) {
      console.log('[bd_list] 调用标点接口失败:', err);
    }
    finally {
      //tt.hideLoading({});
      console.log('[bd_list] 调用标点查询接口结束');
    }
    return res;
  }
}

// 导出biaodian实例
export const biaodian = new biandian();
