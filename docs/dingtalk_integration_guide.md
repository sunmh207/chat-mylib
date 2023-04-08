# 对接钉钉机器人

## 创建机器人应用

访问钉钉后台： https://open-dev.dingtalk.com/fe/app#/corp/robot ， 创建应用

![图片](imgs/dingtalk/1.png)

## 填写机器人信息 
![图片](imgs/dingtalk/2.png)

## 记录应用信息中的 AppSecret
![图片](imgs/dingtalk/3.png)

## 填写服务器出口IP和消息接收地址

接收地址为本软件的接口地址： http://[host]:[port]/dingtalkbot

![图片](imgs/dingtalk/4.png)

## 上线机器人

![图片](imgs/dingtalk/5.png)

## 找一个钉钉内部群，【设置】-【智能群助手】

![图片](imgs/dingtalk/6.png)

## 添加刚创建的机器人

![图片](imgs/dingtalk/7.png)

## 记录Webhook地址
![图片](imgs/dingtalk/8.png)

## 填写IP段和POST地址

其中POST地址为本软件的接口地址： http://[host]:[port]/dingtalkbot

![图片](imgs/dingtalk/9.png)

## 配置.env文件
```commandline
[dingtalk]
webhook_url:{前面记录的 webhook_url}
secret:{前面记录的 AppSecret}
```

## 与机器人聊天

上述步骤完成后，重启系统，可在群可以看到机器人。@机器人与它交流。

![图片](imgs/dingtalk/10.png)