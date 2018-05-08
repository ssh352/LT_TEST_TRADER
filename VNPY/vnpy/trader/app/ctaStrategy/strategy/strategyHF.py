# encoding: UTF-8

"""
测试用策略，暂时只用于hc1805合约的1分钟线
"""


from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)
from datetime import datetime
import numpy as np

########################################################################
class HFStrategy(CtaTemplate):
    """日内趋势跟踪的分钟线策略"""
    className = 'HFStrategy'
    author = u'WTZ'

    # 策略参数
    smaPara = 2          # 计算快线SMA的参数


    trailingPercent = 0.8   # 百分比移动止损


    initDays = 3           # 初始化数据所用的天数
    fixedSize = 1           # 每次交易的数量

    # 策略变量
    CLOSE = 0
    CLOSE_SMA = 0                     # 均价快线


    intraTradeHigh = 0                  # 移动止损用的持仓期内最高价
    intraTradeLow = 0                   # 移动止损用的持仓期内最低价

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'smaPara',
                 'trailingPercent']

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'CLOSE',
               'CLOSE_SMA',]
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos',
                'intraTradeHigh',
                'intraTradeLow']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(HFStrategy, self).__init__(ctaEngine, setting)
        
        # 创建K线合成器对象
        self.bg = BarGenerator(self.onBar)


        #self.am = ArrayManager(self.slowSmaPara+self.difSmaPara+1)

        self.size = self.smaPara+60
        self.count = 0                      # 缓存计数
        self.inited = False                 # True if count>=size



        self.CLOSE = np.zeros(self.size)
        self.CLOSE_SMA = np.zeros(self.size)


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
        """收到Bar推送（必须由用户继承实现）"""
        tmp = self.ctaEngine.mainEngine.dataEngine.getAllPositions()
        countPos = 0
        countPnl = 0
        if tmp:
            for i in tmp:
                if i.direction == u'空' and i.symbol==self.vtSymbol:
                    countPos = countPos - i.position
                    countPnl = countPnl + i.positionProfit
                if i.direction == u'多' and i.symbol==self.vtSymbol:
                    countPos = countPos+i.position
                    countPnl = countPnl + i.positionProfit
        #print countPos,countPnl

        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True

        if bar.datetime.time()>=datetime(2018,5,4,14,55).time() and bar.datetime.time()<datetime(2018,5,4,17,55).time():
            print '----强制平仓------'
            self.cancelAll()
            if countPos < 0:
                self.cover(bar.close+1, abs(countPos))
            elif countPos > 0:
                self.sell(bar.close-1, abs(countPos))
            return





        # 计算指标数值
        self.CLOSE[0:self.size - 1] = self.CLOSE[1:self.size]
        self.CLOSE_SMA[0:self.size - 1] = self.CLOSE_SMA[1:self.size]
        self.CLOSE[-1] = bar.close

        if self.count>1:
            self.CLOSE_SMA[-1] = (self.CLOSE_SMA[-2]*(self.smaPara-1.0)+ self.CLOSE[-1])/self.smaPara
        else:
            self.CLOSE_SMA[-1] = self.CLOSE[-1]

        print self.CLOSE_SMA[-1],self.CLOSE[-1],self.inited,self.count,countPos,self.trading
        if self.CLOSE_SMA[-1] < self.CLOSE_SMA[-2] and self.CLOSE_SMA[-2] > self.CLOSE_SMA[-3]:
            print'-------------------交叉空头-------------------'
        elif self.CLOSE_SMA[-1] > self.CLOSE_SMA[-2] and self.CLOSE_SMA[-2] < self.CLOSE_SMA[-3]:
            print'-------------------交叉多头-------------------'


        if self.trading and self.inited:
            # 判断是否要进行交易
            if self.CLOSE_SMA[-1] < self.CLOSE_SMA[-2] and self.CLOSE_SMA[-2] >self.CLOSE_SMA[-3]:
                if countPos == 0:
                    self.cancelAll()
                    self.writeCtaLog(u'--%s策略模块--开多仓信号'%self.name)
                    self.buy(bar.close, self.fixedSize)
                elif countPos <0:
                    self.cancelAll()
                    self.writeCtaLog(u'--%s策略模块--平空仓开多仓信号'%self.name)
                    self.cover(bar.close, abs(countPos))
                    self.buy(bar.close, self.fixedSize)
            elif self.CLOSE_SMA[-1] > self.CLOSE_SMA[-2] and self.CLOSE_SMA[-2] < self.CLOSE_SMA[-3]:
                if countPos == 0:
                    self.cancelAll()
                    self.writeCtaLog(u'--%s策略模块--开空仓信号'%self.name)
                    self.short(bar.close, self.fixedSize)
                elif countPos>0:
                    self.cancelAll()
                    self.writeCtaLog(u'--%s策略模块--平多仓开空仓信号'%self.name)
                    self.sell(bar.close, abs(countPos))
                    self.short(bar.close, self.fixedSize)


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