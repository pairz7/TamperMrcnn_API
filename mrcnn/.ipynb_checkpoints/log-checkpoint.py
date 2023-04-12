'''训练日志'''
import os
import datetime
import time

from mrcnn.config import Config
class Log(object):
    def __init__(self,logdir):
        self.log_dir=os.path.join(logdir,'train.log')
        self.appendLine("日志创建")


    def appendLog(self,attr,text):
        self.appendLine("%s:    %s"%(attr,str(text)))

    def appendLine(self,text):
        logFile = open(self.log_dir, 'a')
        timeStamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logFile.write("[%s] %s\n" % (timeStamp,str(text)))
        logFile.close()

    def beginTrain(self):
        self.appendLine("开始训练")

    def endTrain(self):
        self.appendLine("结束训练")
        self.appendLog("正常结束","是")

    def logDataset(self,config,train_time,val_time):
        config_text="BackBone->%s   BatchSize->%s"%(config.BACKBONE,config.BATCH_SIZE)
        class_text=config.CLASS
        train_text="数量->%d   加载时间->%fs"%(config.get_train_count(),train_time)
        val_text="数量->%d   加载时间->%fs"%(config.get_val_count(),val_time)
        self.appendLog("Config",config_text)
        self.appendLog("训练类别",str(class_text))
        self.appendLog("训练集",train_text)
        self.appendLog("验证集",val_text)

    def modelTrainStart(self,learning_rate,start_epoch,epochs,layer,workers):
        text="Learning Rate->%f    Epoch:%d->%d    Layers->%s    workers->%d"%(learning_rate,start_epoch,epochs,layer,workers)
        self.appendLog("Train started",text)
        self.startEpoch=start_epoch
        self.startTime=time.time()

    def modelTrainEnd(self,epoch):
        self.endEpoch=epoch
        self.endTime=time.time()
        totalEpoch=self.endEpoch-self.startEpoch+1
        costTime=self.endTime-self.startTime
        averageTime=costTime/totalEpoch
        timeStr="%dh%dm%ds"%(costTime//3600,(costTime%3600)//60,(costTime%3600)%60)
        speedStr="%dh%dm%ds"%(averageTime//3600,(averageTime%3600)//60,(averageTime%3600)%60)
        text="Current epoch->%d    Epoch trained->%d    训练时间->%s    平均速度->%s per epoch"%(epoch,totalEpoch,timeStr,speedStr)
        self.appendLog("Train ended",text)

    def display(self):
        print("\nTrain logs:")
        for a in dir(self):
            if not a.startswith("__") and not callable(getattr(self, a)):
                print("{:30} {}".format(a, getattr(self, a)))
        print("\n")



