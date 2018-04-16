# encoding: UTF-8

"""
测试用策略，暂时只用于hc1805合约的1分钟线

注意事项：
1. 作者不对交易盈利做任何保证，策略代码仅供参考
2. 将IF0000_1min.csv用ctaHistoryData.py导入MongoDB后，直接运行本文件即可回测策略

"""

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)


########################################################################
class testStrategy(CtaTemplate):
    """日内趋势跟踪的分钟线策略"""
    className = 'testStrategy'
    author = u'用Python的交易员'

    # 策略参数
    midEmaPara = 35          # 计算MADK的参数
    dkMaPara = 35        # 计算MADKEMA的参数
    trailingPercent = 0.8   # 百分比移动止损
    initDays = 10           # 初始化数据所用的天数
    fixedSize = 1           # 每次交易的数量

    # 策略变量
    MID_U = 0                        # 最新的均价
    DK = 0                           # 均价指数平均值
    MADK = 0                        # 指数平均值的简单均线
    intraTradeHigh = 0                  # 移动止损用的持仓期内最高价
    intraTradeLow = 0                   # 移动止损用的持仓期内最低价

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'midEmaPara',
                 'dkMaPara',
                 'trailingPercent']    

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'MID_U',
               'DK',
               'MADK',]
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos',
                'intraTradeHigh',
                'intraTradeLow']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(testStrategy, self).__init__(ctaEngine, setting)
        
        # 创建K线合成器对象
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(90)
        
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）        

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
    


        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        print 'GET BAR----TEST-----'
        #print bar
        """收到Bar推送（必须由用户继承实现）"""
        self.cancelAll()

        # 保存K线数据
        am = self.am
        am.updateBar(bar)
        if not am.inited:
            return

        # 计算指标数值
        DkArray,MadkArray = am.madk_ema(self.dkMaPara,self.midEmaPara, array=True)
        # self.DkValue = DkArray[-1]
        # self.atrMa = MadkArray[-1]
        # 判断是否要进行交易
        
        # 当前无仓位
        print '------最新指标------',DkArray[-1],MadkArray[-1]
        # if DkArray[-2] < MadkArray[-2] and  DkArray[-1] > MadkArray[-1]:
        #     print '开多仓'
        #     if self.pos >= 0:
        #         self.buy(bar.close + 5, self.fixedSize)
        #     else:
        #         self.cover(bar.close + 5, abs(self.pos))
        #         self.buy(bar.close + 5, self.fixedSize)
        # elif DkArray[-2] > MadkArray[-2] and  DkArray[-1] < MadkArray[-1]:
        #     print '开空仓'
        #     if self.pos <= 0:
        #         self.short(bar.close - 5, self.fixedSize)
        #     else:
        #         self.sell(bar.close - 5, abs(self.pos))
        #         self.short(bar.close - 5, self.fixedSize)

        if DkArray[-1] > MadkArray[-1]:
            if self.pos == 0:
                print '开多仓'
                self.buy(bar.close + 10, self.fixedSize)
            elif self.pos <0:
                print '平空仓开多仓'
                self.cover(bar.close + 10, abs(self.pos))
                self.buy(bar.close + 10, self.fixedSize)
        elif DkArray[-1] < MadkArray[-1]:
            if self.pos == 0:
                print '开空仓'
                self.short(bar.close - 10, self.fixedSize)
            elif self.pos>0:
                print '平多仓开空仓'
                self.sell(bar.close - 10, abs(self.pos))
                self.short(bar.close - 10, self.fixedSize)










        # if self.pos == 0:
        #     self.intraTradeHigh = bar.high
        #     self.intraTradeLow = bar.low
        #
        #     # ATR数值上穿其移动平均线，说明行情短期内波动加大
        #     # 即处于趋势的概率较大，适合CTA开仓
        #     if self.atrValue > self.atrMa:
        #         # 使用RSI指标的趋势行情时，会在超买超卖区钝化特征，作为开仓信号
        #         if self.rsiValue > self.rsiBuy:
        #             # 这里为了保证成交，选择超价5个整指数点下单
        #             self.buy(bar.close+5, self.fixedSize)
        #
        #         elif self.rsiValue < self.rsiSell:
        #             self.short(bar.close-5, self.fixedSize)
        #
        # # 持有多头仓位
        # elif self.pos > 0:
        #     # 计算多头持有期内的最高价，以及重置最低价
        #     self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
        #     self.intraTradeLow = bar.low
        #
        #     # 计算多头移动止损
        #     longStop = self.intraTradeHigh * (1-self.trailingPercent/100)
        #
        #     # 发出本地止损委托
        #     self.sell(longStop, abs(self.pos), stop=True)
        #
        # # 持有空头仓位
        # elif self.pos < 0:
        #     self.intraTradeLow = min(self.intraTradeLow, bar.low)
        #     self.intraTradeHigh = bar.high
        #
        #     shortStop = self.intraTradeLow * (1+self.trailingPercent/100)
        #     self.cover(shortStop, abs(self.pos), stop=True)

        # 同步数据到数据库
        self.saveSyncData()

        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass