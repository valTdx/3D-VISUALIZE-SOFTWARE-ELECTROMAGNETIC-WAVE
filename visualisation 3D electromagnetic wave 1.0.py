"""
Program to plot 3D wave with a GUI
version : 1.0
date : 06/2021
author : Valentin Tardieux
"""
import numpy as np
import sys
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar)
## Global Variables

#Animation parameters
animParameters={'nPoint':360,'interval':30,'repeat':True,'repeat_delay':0,'nVector':1,'fragmentedNoPlotLen':5,'fragmentedPlotLen':10,'fps':60,'writer':'imagemagick'} #Warning : nPoint>nVector !

#dictionary with different sate : {'name' (str):initial_state(bool)}
state={'vector':True,'timeTrack':False,'vectorTrack':False,'static':True,'autoscale':True,'fragmented':False}

#Frequency & amplitude parameters for each axis, updated thanks to the GUI:
parametersName=['frequency x','frequency y','frequency z','amplitude x','amplitude y','amplitude z','phase x','phase y','phase z','offset x','offset y','offset z']
waveParameters={'frequency x':2,'frequency y':2,'frequency z':0,'amplitude x':1,'amplitude y':1,'amplitude z':1,'phase x':0,'phase y':np.pi/2,'phase z':0,'offset x':0,'offset y':0,'offset z':0}

#Preset rules : {'name of the figure' : [fx,fy,fz,Ax,Ay,Az,Phix,Phiy,Phiz,offsetx,offsety,offsetz]}
presetParameters={'Flat Disk':['frequency x','frequency x',0,'amplitude x','amplitude x',0,0,np.pi/2,0,0,0,0],'Wide Cone':['frequency x','frequency x',0,'amplitude x','amplitude y','amplitude z',0,'phase y',0,0,0,0],'Small Cone':['frequency x','frequency x',0,'amplitude x','amplitude x','amplitude z',0,'phase y',0,0,0,0],'Permanent Magnet':[0,0,0,'amplitude x','amplitude y','amplitude z','phase x','phase y','phase z',0,0,0],'Pendulum':['frequency x','frequency x',0,'amplitude x','amplitude y','amplitude z',0,0,0,0,0,0],'Swinging Rotation':['frequency x','frequency x','frequency z','amplitude x','amplitude x','amplitude z',0,np.pi/2,0,0,0,0],'Alternating':[0,0,'frequency z',0,0,'amplitude z',0,0,0,0,0,0],'Alternating + Constant':[0,0,'frequency z',0,0,'amplitude z',0,0,0,0,0,'offset z'],'Free Mode':parametersName}

#Only values for parameters independant and can be changed
wavePresetValue={'Flat Disk':[None]*12,'Wide Cone':[1,2,2,3,np.pi/2],'Small Cone':[1,1,10,np.pi/2],'Permanent Magnet':[1,2,3,0,0,0],'Pendulum':[1,1,2,1],'Swinging Rotation':[1,10,5,1],'Alternating':[3,2],'Alternating + Constant':[3,4,2],'Free Mode':[None]*12}

#Type of function generated
def B(freq,amplitude,phi,dt,**kwargs):
    K=kwargs.get('offset',0)
    return amplitude*np.cos(2*np.pi*freq*dt/animParameters['nPoint']+phi)+K

## Windows
#Canvas where animation object is displayed
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=500, height=400, dpi=100):
        fig=Figure(figsize=(width, height), dpi=dpi)
        self.fig=fig
        super(MplCanvas, self).__init__(fig)
        self.ax = fig.subplots(subplot_kw={'projection': '3d'})
        self.ax.grid(False)
        self.vectorTrackFig=[[]for i in range(animParameters['nPoint'])]
        self.Barray=self.Bgen()
        self.resizeVect()
        self.figDic={'track':self.ax.plot([],[],[],color='green'),'static':self.ax.plot([],[],[],color='blue')}
        self.anim()
    def anim(self):
        """
        Call funcAnimation of animation module which call update
        """
        def update(frame):
            """
            frame : iterator object
            Select in function of the state the plot wanted
            """
            #Maximum of amplitude of one axe set the scale for the other
            if(state['autoscale']):
                lim=max(waveParameters['amplitude x']+waveParameters['offset x'],waveParameters['amplitude y']+waveParameters['offset y'],waveParameters['amplitude z']+waveParameters['offset z'])
                self.ax.set_xlim3d(-lim,lim)
                self.ax.set_ylim3d(-lim,lim)
                self.ax.set_zlim3d(-lim,lim)
            #3 plots avaible monitored by a checkbox:
            if(state['vectorTrack']):
                self.plotVectorTrack(animParameters['nVector'],frame)
            if(state['vector'] and not(state['vectorTrack'])):
                self.plotVectorTrack(1,frame)
                #Vector : plot a vector between (0,0) and the point (x,y,z) at t
            if(state['static']):
                self.plotStatic()
                #Stationary : plot the entire  signal
            if(state['timeTrack']):
                self.plotTimeTrack(frame)
                #Track : plot frame by frame the signal
            return self.figDic['track'][0],self.figDic['static'][0],self.vectorTrackFig
        self.animation = animation.FuncAnimation(self.fig, update,frames=animParameters['nPoint'], blit=False,interval=animParameters['interval'],repeat=animParameters['repeat'],save_count=animParameters['nPoint'],repeat_delay=animParameters['repeat_delay']) #function of matplotlib module, call update at each frame, call init for the first frame

    def Bgen(self):
        """
        Generate a new array thanks to B function
        """
        coord=np.empty((3,animParameters['nPoint']),dtype=float)
        for t in range(0,animParameters['nPoint']):
            coord[0][t]=B(waveParameters['frequency x'],waveParameters['amplitude x'],waveParameters['phase x'],t,offset=waveParameters['offset x'])
            coord[1][t]=B(waveParameters['frequency y'],waveParameters['amplitude y'],waveParameters['phase y'],t,offset=waveParameters['offset y'])
            coord[2][t]=B(waveParameters['frequency z'],waveParameters['amplitude z'],waveParameters['phase z'],t,offset=waveParameters['offset z'])

        #When fragmented is enabled
        if(state['fragmented']):
            totalLen=int(animParameters['fragmentedNoPlotLen']+animParameters['fragmentedPlotLen'])
            step=int(animParameters['nPoint']/totalLen)
            bfragmented=np.zeros((3,animParameters['nPoint']),dtype=float)
            plotLen=animParameters['fragmentedPlotLen']
            for i in range(step):
                bfragmented[0][i*totalLen:i*totalLen+plotLen]=coord[0][i*totalLen:i*totalLen+plotLen]
                bfragmented[1][i*totalLen:i*totalLen+plotLen]=coord[1][i*totalLen:i*totalLen+plotLen]
                bfragmented[2][i*totalLen:i*totalLen+plotLen]=coord[2][i*totalLen:i*totalLen+plotLen]
            coord=bfragmented
        return coord

    def plotVectorTrack(self,nVect,time):
        '''
        Plot nVect vector
        attenuation decreasing in 1/nVect, last vector ploted has a attenuation of 1 then decreasing
        '''
        ind=time%nVect #time modulo number of vector(ie. time module number of vector plot in resize function)
        self.vectorTrackFig[ind][0].set_data_3d([0,self.Barray[0][time]],[0,self.Barray[1][time]],[0,self.Barray[2][time]])#Set new data for the plot at the index ind with the current time
        self.opacity(self.vectorTrackFig,nVect,ind)

    def opacity(self,plotArray,nArray,ind):
        transparencyInterval=1/nArray #step of transparency
        indT=(ind+1)%nArray #index for transparency, start with the lower opacity(ie the last index of our array
        count=1 #count turn number of loop while did
        while(count<nArray+1):
            plotArray[indT][0].set_alpha(count*transparencyInterval)#set opacity
            count+=1
            indT+=1 #3 lines : ie indT+1 modulo nArray
            if(indT==nArray):
                indT=0
    def plotStatic(self):
        self.figDic['static'][0].set_data_3d(self.Barray)

    def plotTimeTrack(self,time):
        self.figDic['track'][0].set_data_3d(self.Barray[0][:time],self.Barray[1][:time],self.Barray[2][:time])

    def func_clear(self):
        '''clear draw and reset coord '''
        self.animation.pause()
        #reset frame
        self.animation.frame_seq=self.animation.new_frame_seq()
        #delete former values computed
        self.initCoord(self.figDic['track'][0])
        self.initCoord(self.figDic['static'][0])
        # self.initVect(animParameters['nVector'])
        self.resizeVect()
        self.animation.resume()
    def initVect(self,nbVector):
        for i in range(nbVector):
            self.initCoord(self.vectorTrackFig[i][0])
    def initCoord(self,name):
    #Reset values for each axis
        name.set_data_3d([],[],[])
    def resizeVect(self):
        #Compute the previous size
        indPrevSize=0
        while(self.vectorTrackFig[indPrevSize]!=[]):
            indPrevSize+=1
        #Reset previous coord
        self.initVect(indPrevSize)
        for indNewPlot in range(indPrevSize,animParameters['nVector']):
            self.vectorTrackFig[indNewPlot]=self.ax.plot([],[],[],'->',color='red')

        #Delete slot if new nVector is inferior to the previous
        for indRemovePlot in range(animParameters['nVector'],indPrevSize):
            self.vectorTrackFig[indRemovePlot]=[]

    def markerChanged(self,marker,line):
        for figName in self.figDic:
            self.figDic[figName][0].set_marker(marker)
            self.figDic[figName][0].set_linestyle(line)

    def stopAnim(self):
        self.animation.repeat=False
        self.animation.__del__()


#CheckBox
class CheckBoxCustom(QtWidgets.QCheckBox):
    def __init__(self,name,status,visu,window):
        super().__init__(name)
        self.status=status
        self.visu=visu
        self.w=window
        self.setChecked(state[self.status])
        self.toggled.connect(self.stateSwitch)

    def stateSwitch(self):
        global state
        state[self.status]=not(state[self.status])
        if(self.status=='static'):
            self.visu.initCoord(self.visu.figDic['static'][0])
        if(self.status=='timeTrack'):
            self.visu.initCoord(self.visu.figDic['track'][0])
        if(self.status=='vectorTrack' or self.status=='vector'):
            self.visu.initVect(animParameters['nVector'])
        if(self.status=='fragmented'):
            if(state[self.status]):
                self.visu.markerChanged('.','')
            else:
                self.visu.markerChanged('','-')
            self.w.noise_spinPlotLen.setEnabled(state[self.status])
            self.w.noise_spinNoPlotLen.setEnabled(state[self.status])
            self.visu.Barray=self.visu.Bgen()


class PresetList(QtWidgets.QListWidget):

    def __init__(self,window,list):
        super().__init__()
        self.w=window
        self.list=list
        for l in self.list:
            self.addItem(l)
        self.currentItemChanged.connect(self.presetPush)
        self.setCurrentRow(0)

    def presetActBox(self,box,nameBox,presetValue,namePreset,indPreset):
        spinBox=box[nameBox]
        ind=0
        if(type(presetValue)==str):
            spinBox.setEnabled(True)
            if(nameBox!=presetValue):
                spinBox.setReadOnly(True)
            else:
                spinBox.setReadOnly(False)
            spinBox.setValue(box[presetValue].value())
        else:
            spinBox.setValue(presetValue)
            spinBox.setEnabled(False)
        return indPreset

    def presetPush(self):
        #Initialize with default values
        indPreset=0
        presetName=self.currentItem()
        presetName=presetName.text()
        preset=self.list[presetName]
        for i in range(len(parametersName)):
            if(type(preset[i])==str):
                if(parametersName[i]==preset[i]):
                    defaultValue=wavePresetValue[presetName][indPreset]
                    if(defaultValue!=None):
                        self.w.parametersBox[parametersName[i]].setValue(defaultValue)
                    indPreset+=1
        self.presetInit()

    def presetInit(self):
        #Create rules for SpinBox
        presetName=self.currentItem()
        presetName=presetName.text()
        preset=self.list[presetName]
        indDefaultValue=0
        #set parameters with rules selected
        for i in range(len(parametersName)):
            self.w.parametersBox[parametersName[i]].disconnect()
            indDefaultValue=self.presetActBox(self.w.parametersBox,parametersName[i],preset[i],presetName,indDefaultValue)

        #gen a new B function
        for name in self.w.parametersBox:
            waveParameters[name]=self.w.parametersBox[name].value()
            self.w.parametersBox[name].valueChanged.connect(self.presetInit)
        self.w.visu.Barray=self.w.visu.Bgen()
        self.w.visu.func_clear()


#Parameters box : allows to set new value for frequency and amplitude
class ParametersBox(QtWidgets.QDoubleSpinBox):

    def __init__(self,name,visu,w):
        super().__init__()
        self.name=name
        self.visu=visu
        self.w=w
        self.setValue(waveParameters[self.name])
        self.setPrefix(self.name[-1]+' : ')
        self.setMaximum(animParameters['nPoint'])
        self.valueChanged.connect(self.change)

    def change(self):
        self.w.preset_list.presetInit()


#Main window
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle('3D Visualize')

        #left panel : visual
        self.visu = MplCanvas(self, width=500, height=400, dpi=150)
        lpanel=QtWidgets.QVBoxLayout()
        lpanel.addWidget(NavigationToolbar(self.visu, self))
        lpanel.addWidget(self.visu)

        #right panel : User controls
        rpanel=QtWidgets.QVBoxLayout()
        #Frequency :
        freq_panel=QtWidgets.QHBoxLayout()
        freq_label=QtWidgets.QLabel('Frequency :')
        freqX_box=ParametersBox('frequency x',self.visu,self)
        freqY_box=ParametersBox('frequency y',self.visu,self)
        freqZ_box=ParametersBox('frequency z',self.visu,self)
        freq_panel.addWidget(freq_label)
        freq_panel.addWidget(freqX_box)
        freq_panel.addWidget(freqY_box)
        freq_panel.addWidget(freqZ_box)
        self.frequency={'frequency x':freqX_box,'frequency y':freqY_box,'frequency z':freqZ_box}
        rpanel.addLayout(freq_panel)
        #Amplitude :
        amp_panel=QtWidgets.QHBoxLayout()
        amp_label=QtWidgets.QLabel('Amplitude :')
        ampX_box=ParametersBox('amplitude x',self.visu,self)
        ampY_box=ParametersBox('amplitude y',self.visu,self)
        ampZ_box=ParametersBox('amplitude z',self.visu,self)
        amp_panel.addWidget(amp_label)
        amp_panel.addWidget(ampX_box)
        amp_panel.addWidget(ampY_box)
        amp_panel.addWidget(ampZ_box)
        self.amplitude={'amplitude x':ampX_box,'amplitude y':ampY_box,'amplitude z':ampZ_box}
        rpanel.addLayout(amp_panel)
        #Phase
        phase_panel=QtWidgets.QHBoxLayout()
        phase_label=QtWidgets.QLabel('Phase (rad) :')
        phaseX_box=ParametersBox('phase x',self.visu,self)
        phaseY_box=ParametersBox('phase y',self.visu,self)
        phaseZ_box=ParametersBox('phase z',self.visu,self)
        phase_panel.addWidget(phase_label)
        phase_panel.addWidget(phaseX_box)
        phase_panel.addWidget(phaseY_box)
        phase_panel.addWidget(phaseZ_box)
        self.phase={'phase x':phaseX_box,'phase y':phaseY_box,'phase z':phaseZ_box}
        rpanel.addLayout(phase_panel)
        #Offset
        offset_panel=QtWidgets.QHBoxLayout()
        offset_label=QtWidgets.QLabel('Offset :')
        offsetX_box=ParametersBox('offset x',self.visu,self)
        offsetY_box=ParametersBox('offset y',self.visu,self)
        offsetZ_box=ParametersBox('offset z',self.visu,self)
        offset_panel.addWidget(offset_label)
        offset_panel.addWidget(offsetX_box)
        offset_panel.addWidget(offsetY_box)
        offset_panel.addWidget(offsetZ_box)
        self.offset={'offset x':offsetX_box,'offset y':offsetY_box,'offset z':offsetZ_box}
        rpanel.addLayout(offset_panel)
        self.parametersBox=self.frequency|self.amplitude|self.phase|self.offset
        #Space
        spaceLayout=QtWidgets.QVBoxLayout()
        spaceLayout.setContentsMargins(0,10,0,10)
        rpanel.addLayout(spaceLayout)
        #Signal fragmented
        noise_panel=QtWidgets.QGridLayout()
        noise_label=QtWidgets.QLabel('Fragmented plot : ')

        noise_check=CheckBoxCustom('Enabled','fragmented',self.visu,self)
        def spinfragmentedPlot():
            self.noise_spinPlotLen.setMaximum(animParameters['nPoint']-animParameters['fragmentedNoPlotLen'])
            animParameters['fragmentedPlotLen']=self.noise_spinPlotLen.value()
            self.visu.func_clear()
            self.visu.Barray=self.visu.Bgen()
        def spinfragmentedNo():
            self.noise_spinPlotLen.setMaximum(animParameters['nPoint']-animParameters['fragmentedPlotLen'])
            animParameters['fragmentedNoPlotLen']=self.noise_spinNoPlotLen.value()
            self.visu.func_clear()
            self.visu.Barray=self.visu.Bgen()
        self.noise_spinPlotLen=QtWidgets.QSpinBox()
        self.noise_spinPlotLen.setEnabled(False)
        self.noise_spinPlotLen.setMaximum(animParameters['nPoint'])
        self.noise_spinNoPlotLen=QtWidgets.QSpinBox()
        self.noise_spinNoPlotLen.setMaximum(animParameters['nPoint']-animParameters['fragmentedPlotLen'])
        self.noise_spinPlotLen.setValue(animParameters['fragmentedPlotLen'])
        self.noise_spinNoPlotLen.setValue(animParameters['fragmentedNoPlotLen'])
        self.noise_spinPlotLen.valueChanged.connect(lambda x: spinfragmentedNo())
        self.noise_spinNoPlotLen.valueChanged.connect(lambda x: spinfragmentedPlot())
        self.noise_spinNoPlotLen.setEnabled(False)
        noise_panel.addWidget(noise_label,1,2,1,1)
        noise_panel.addWidget(noise_check,2,2)
        noise_panel.addWidget(QtWidgets.QLabel('Len of plot : '),1,3)
        noise_panel.addWidget(self.noise_spinPlotLen,2,3)
        noise_panel.addWidget(QtWidgets.QLabel('Len of no plot : '),1,4)
        noise_panel.addWidget(self.noise_spinNoPlotLen,2,4)
        noise_panel.setAlignment(QtCore.Qt.AlignTop)
        rpanel.addLayout(noise_panel)
        #Space
        spaceLayout=QtWidgets.QVBoxLayout()
        spaceLayout.setContentsMargins(0,20,0,20)
        rpanel.addLayout(spaceLayout)
        #Preset shape
        preset_panel=QtWidgets.QVBoxLayout()
        preset_label=QtWidgets.QLabel('Preset :')
        preset_label.setAlignment(QtCore.Qt.AlignCenter)
        self.preset_list=PresetList(self,presetParameters)
        preset_panel.addWidget(preset_label)
        preset_panel.addWidget(self.preset_list)
        preset_panel.setContentsMargins(0,0,0,40)
        rpanel.addLayout(preset_panel)
        #Vector panel
        vector_panel=QtWidgets.QHBoxLayout()
        vector_label=QtWidgets.QLabel('Vector settings')
        vector_check=CheckBoxCustom('Vector','vector',self.visu,self)
        vectorTrack_check=CheckBoxCustom('Vector with track','vectorTrack',self.visu,self)
        vector_box=QtWidgets.QSpinBox()
        vector_box.setPrefix('Track length :   ')
        vector_box.setMaximum(int(animParameters['nPoint']/2))
        vector_box.setMinimum(1)
        vector_box.setValue(animParameters['nVector'])
        def vectorBoxValueChanged(visu):
            self.visu.animation.pause()
            # self.visu.initVect(animParameters['nVector'])
            animParameters['nVector']=vector_box.value()
            self.visu.resizeVect()
            self.visu.animation.resume()
        vector_box.valueChanged.connect(lambda x: vectorBoxValueChanged(self.visu))
        vector_panel.addWidget(vector_label)
        vector_panel.addWidget(vector_check)
        vector_panel.addWidget(vectorTrack_check)
        vector_panel.addWidget(vector_box)
        vector_panel.setContentsMargins(0,0,0,40)
        rpanel.addLayout(vector_panel)

        #Custom panel
        custom_panel=QtWidgets.QVBoxLayout()
        track_check=CheckBoxCustom('Time Tracker','timeTrack',self.visu,self)
        static_check=CheckBoxCustom('Static state','static',self.visu,self)
        autoscale_check=CheckBoxCustom('Auto-scale','autoscale',self.visu,self)
        custom_panel.addWidget(track_check)
        custom_panel.addWidget(static_check)
        custom_panel.addWidget(autoscale_check)
        custom_panel.setAlignment(QtCore.Qt.AlignCenter)
        custom_panel.setContentsMargins(0,0,0,30)
        rpanel.addLayout(custom_panel)

        #Control panel
        control_panel=QtWidgets.QHBoxLayout()
        clear_button=QtWidgets.QPushButton('Clear and reset animation')
        pause_button=QtWidgets.QPushButton('Pause')
        resume_button=QtWidgets.QPushButton('Resume')
        clear_button.clicked.connect(self.visu.func_clear)
        pause_button.clicked.connect(lambda a:self.visu.animation.pause())
        resume_button.clicked.connect(lambda a:self.visu.animation.resume())
        control_panel.addWidget(pause_button)
        control_panel.addWidget(resume_button)
        control_panel.addWidget(clear_button)
        control_panel.setAlignment(QtCore.Qt.AlignBottom)
        control_panel.setContentsMargins(0,0,0,10)
        rpanel.addLayout(control_panel)

        #Export panel
        exp_panel=QtWidgets.QHBoxLayout()
        def record():
            filePath=QtWidgets.QFileDialog.getSaveFileName(None,'Save as...','visualize','*.mp4 *.gif')[0]
            if(filePath!=''):
                self.visu.animation.repeat=False
                self.visu.animation.save(filePath, writer=animParameters['writer'], fps=animParameters['fps'])
                self.visu.animation.frame_seq=self.visu.animation.new_frame_seq()
                self.visu.animation.repeat=True
                self.visu.func_clear()
        exp_button=QtWidgets.QPushButton('Export animation')
        exp_button.clicked.connect(lambda r:record())
        exp_panel.addWidget(exp_button)
        exp_panel.setContentsMargins(0,0,0,10)
        rpanel.addLayout(exp_panel)

        #Position of panels
        panel=QtWidgets.QHBoxLayout()
        panel.addLayout(lpanel)
        panel.addLayout(rpanel)
        widget = QtWidgets.QWidget()
        widget.setLayout(panel)
        self.setCentralWidget(widget)
        self.show()
    def closeEvent(self,event):
        self.visu.stopAnim()
#Shows main window
def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
if __name__=='__main__':
    main()