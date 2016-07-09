---
layout: post
title: "R6250刷梅林固件救砖及刷回原厂"
date: "2016-06-25 00:45:25 +0800"
tags: [Geek, Netgear, Router, 折腾]
category: 折腾
toc: true
---

前些天买了一个网件R6250路由器, 5G性能覆盖都相当给力， 爽了几天，终于忍不住手贱开始折腾，刷了梅林固件[^netgear-merlin]，然后就很不幸地……砖了，开机闪黄灯，自动进了tftp模式，tftp传固件进去没反应， ping过去ttl始终是100（ping路由器ttl=100表示恢复模式，ttl=64表示正常）。倒腾过不少路由器，刷砖了还是第一次，趴了一阵帖子，发现基本上得靠tty了。刷过之后感受了两天，感觉功能非常的强大，但是稳定性非常之不靠谱，老妈意见比较大，还是决定刷回原厂固件，没想到又是一番波折，在这里记录一下，希望能帮到后来者。

### TFTP救砖

我刷机时参考的帖子是[这个](http://www.hkepc.com/forum/viewthread.php?fid=12&tid=2264167)， 相关的固件可以在里面下载，另外[koolshare](http://koolshare.cn/forum-72-1.html)也有相关固件, 请参考R6300V2的刷机教程。

因为刷梅林会改写机器的`board_id`和`CFE`（内置shell）刷梅林又需要好几个过渡固件，因此会导致固件校验不过, 无法写入, 在不进入tty的情况下我们无法得知当前的board_id，因此先进行以下尝试：

1. 如果你的路由器依然可以tftp，请以此尝试tftp刷入以下固件:
    - R6250原厂固件 [下载](http://www.downloads.netgear.com/files/GDC/R6250/R6250-V1.0.4.2_10.1.10.zip)
    - R6300V2原厂固件 [下载](http://www.downloads.netgear.com/files/GDC/R6300V2/R6300v2-V1.0.4.2_10.0.74.zip)
    - R6300V2-back-to-ofw.trx
    - factory-to-dd-wrt.chk 
    - R6300V2_merlin_1.0.trx
    - R6300V2_merlin_1.2.trx
    - R6300V2_378.56_0-X5.9.trx (或其他更新版本的固件)

2. 如果不能tftp，直接往下看吧

### TTY

如果你还没有tty线，请上淘宝买一根，一般的USB-tty或者串口线都可以, 如果你没有拆机螺丝刀和电烙铁记得也买一套

打开机器，参考下图进行接线（图是盗的, 见参考）:

![r6250-tty](/images/r6250-tty.jpg)

- G = GND
- R = RXD
- T = TXD

因为R6250偷工减料地省了杜邦插座（r6300是有的），因此需要把线焊在电路板上

然后就可以连到路由器的tty了，OSX/Linux下可以使用[minicom](http://mstempin.free.fr/linux-ipaq/html/minicom-setup.html)

Windows下可以使用putty

具体使用方法不再赘述，请自行上网查找

连接参数：

```
Speed: 115200
Stopbits: 8-N-1
```

打开连接后启动路由器， 就可以看到终端里狂刷消息了，如果路由器还在恢复模式中（黄灯闪），开机时候多按几下`Ctrl-C`即可进入路由器内置shell（CFE）

则将网线接上LAN口，设固定IP `192.168.1.2`, 输入`tftpd`回车，然后重复上面 [TFTP救砖](#TFTP救砖)部分的步骤

### 刷回原厂固件

原本以为刷回原厂会比较简单, 因为[这个帖子](http://www.hkepc.com/forum/viewthread.php?fid=12&tid=2264167)里提供了`R6250-back-to-ofw.trx`的固件说是可以直接在梅林界面上刷回去

但是我刷进去却被梅林固件拒绝了，因为刷过梅林之后，机器已经被识别为R6300V2，刷个R6250的固件进去，被校验机制拦截了，尝试了几次均不成功，最后决定冒险刷一下`R6300V2_back-to-ofw.trx`, 居然一次成功

刷完之后十分顺利地进入了原厂网件的界面，但是发现仍然被识别为了R6300V2（怎么感觉好像有点赚到了），测试了一下基本正常，但是一些界面有些不太对，5G的频道不能选，默认频道比较低，5G速度不行，系统能找到固件升级，但是下载下来却报固件损坏无法写入。这时在Web界面上，无论是刷梅林，R6300V2，R6250，还是DD-WRT均不成功，任何固件都不认。

虽然路由器能用了，似乎也还比较稳定，但是完美主义的毛病又犯了，搞个半残的路由器总让人很不爽，想着还是要解决掉这个问题。思考了一下，想到之前在TTY中使用 `nvram get board_id` 查看 `board_id` 时返回的结果是HDR0，也就是没有board_id的状态，想过去应该board_id校验失败了，只要能想办法刷掉board_id，应该就有救, 一番扒贴之后在[这里](https://community.netgear.com/t5/Nighthawk-WiFi-Routers/SOLVED-Steps-for-debrick-unresponsive-R7000-softbricked/td-p/414034/page/2), 找到了原厂固件的telnet console自带一个`burnboardid`命令可以写入board_id, 看来还有救。

网件有后门可以打开telnet console, [openwrt wiki](https://wiki.openwrt.org/toh/netgear/telnet.console)上有相关的指导，但是我没有成功，如果有人成功了麻烦告知一下。

进不了telnet我们还有tty线，参考上一节tty的部分, 连进机器, 使用命令写入board_id

```bash
burnboardid U12H245T00_NETGEAR
```

重启，刷6250固件， 成功！终于恢复原厂固件了

不过再进系统，发现还是有些不正常，一些界面不太对，wifi地区可以选择但无效，继续研究，发现有一系列的burn命令:

```
burn_hw_rev
burn5gpass
burn5gssid
burnboardid
burnethermac
burnpass
burnpin
burnrf
burnsku
burnsn
burnssid
```

一个一个查看过去（命令不输参数则显示当前值）, 发现sn和pin值显示为乱码，应该要写入一个正确的值:

```bash
burnsn XXXXXXXXXX # SN可以在机器底部的条形码上找到(SERIAL NUMBER)
burnpin XXXXXXXX # 随便写8位数字，路由器的PIN码，写入的值在路由器的设置界面可以看到
```

重启， 一切正常！

#### 一点bonus

我的路由器买的是水货，区域只能选择美国，可以选择的频段有限，我们可以用

```bash
burnsku 0x0002
```

命令来将路由器刷成WW(World Wide)版的，这样路由器就变成全区的了，wifi界面的地区可以随便选了

另外，`burnrf` 命令仍然返给我一个报错，不过好像也没有影响。没有找到相关资料，如果有知道的麻烦告知一下。

### 参考

- [How to Debrick or Recover NETGEAR R7000, R6300v2, or R6250 Wi-Fi Routers](http://myopenrouter.com/article/how-debrick-or-recover-netgear-r7000-r6300v2-or-r6250-wi-fi-routers)
- [网件R6250变砖恢复记~](http://tieba.baidu.com/p/4309478736)
- [所有区域码(burnsku用)](http://www.dd-wrt.com/phpBB2/viewtopic.php?p=918458&sid=8bb156a5caff7b11fb6f8a6b73971dcf)


[^netgear-merlin]: 如果有人对刷梅林感兴趣，R6250是没有专用的梅林的，但是可以直接刷R6300V2的固件，可以参考[这个链接](http://www.hkepc.com/forum/viewthread.php?fid=12&tid=2264167)， 但我刷了之后感觉稳定性欠佳，特别是2.4G基本处于不能用状态，所以还是刷回来。帖子里的固件版本较旧，更加不稳定，可以在[这里](http://koolshare.io/merlin_8wan_firmware/R6300V2/)下载最新版的固件
