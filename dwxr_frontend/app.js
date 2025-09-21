App({
    globalData: {
        category: 0,
        openid: null
    },
    onLaunch: function() {
        const systemInfo = tt.getSystemInfoSync();
        this.setGlobalData('systemInfo', systemInfo)
    },
    getPhoneNumber({
        params,
        success,
        fail
    }) {
        const {
            iv,
            encryptedData
        } = params;
        // ...
        // 开发者服务端解密 encryptedData，得到手机号
        // ...
        const result = {
            phoneNumber: '18133842224',
        }
        // 回调前端模板
        success(result)
    },
    setGlobalData(key, value) {
        this.globalData[key] = value;
    },
    getGlobalData(key) {
        return this.globalData[key];
    }
})