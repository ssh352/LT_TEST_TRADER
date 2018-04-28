# encoding: UTF-8

"""
测试用策略，暂时只用于hc1805合约的1分钟线
"""


from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)


########################################################################
class simpleTradeStrategy(CtaTemplate):
    """日内趋势跟踪的分钟线策略"""
    className = 'simpleTradeStrategy'
    author = u'WTZ'

    # 策略参数
    fastSmaPara = 83          # 计算快线SMA的参数
    slowSmaPara = 98          # 计算慢线SMA的参数
    difSmaPara = 23           # 计算difSMA的参数


    trailingPercent = 0.8   # 百分比移动止损


    initDays = 3           # 初始化数据所用的天数
    fixedSize = 1           # 每次交易的数量

    # 策略变量
    MID_U = 0                        # 最新的均价
    MID_FAST = 0                     # 均价快线
    MID_SLOW = 0                     # 均价慢线
    DIF = 0                          #快慢线差值
    DIF_MA = 0                           #快慢线差值均线


    intraTradeHigh = 0                  # 移动止损用的持仓期内最高价
    intraTradeLow = 0                   # 移动止损用的持仓期内最低价

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'fastSmaPara',
                 'slowSmaPara',
                 'difSmaPara',
                 'trailingPercent']    

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'MID_U',
               'MID_FAST',
               'MID_SLOW',
               'DIF',
               'DIF_MA',]
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos',
                'intraTradeHigh',
                'intraTradeLow']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(simpleTradeStrategy, self).__init__(ctaEngine, setting)
        
        # 创建K线合成器对象
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(self.slowSmaPara+self.difSmaPara+1)
        
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
        self.cancelAll()

        # 保存K线数据
        am = self.am
        am.updateBar(bar)
        if not am.inited:
            return

        # 计算指标数值
        DIF, DIF_SMA = am.sma_dif(self.fastSmaPara,self.slowSmaPara,self.difSmaPara, array=True)
        if self.trading:
            # 判断是否要进行交易
            if DIF[-1] > DIF_SMA[-1]:
                if self.pos == 0:
                    self.writeCtaLog(u'--%s策略模块--开多仓信号'%self.name)
                    self.buy(bar.close + 10, self.fixedSize)
                elif self.pos <0:
                    self.writeCtaLog(u'--%s策略模块--平空仓开多仓信号'%self.name)
                    self.cover(bar.close + 10, abs(self.pos))
                    self.buy(bar.close + 10, self.fixedSize)
            elif DIF[-1] < DIF_SMA[-1]:
                if self.pos == 0:
                    self.writeCtaLog(u'--%s策略模块--开空仓信号'%self.name)
                    self.short(bar.close - 10, self.fixedSize)
                elif self.pos>0:
                    self.writeCtaLog(u'--%s策略模块--平多仓开空仓信号'%self.name)
                    self.sell(bar.close - 10, abs(self.pos))
                    self.short(bar.close - 10, self.fixedSize)
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