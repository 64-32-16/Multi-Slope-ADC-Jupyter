






#---------------------------------------------------------------------------------------
# Simulation für einen Multi Slope ADC.
#
# Fogende Phasen der Messung sind implementiert
# * RunUp Phase
# * RunDown Phase
# * ResidueADC
# * Calc Vin
#---------------------------------------------------------------------------------------
# 28.12.2024 AutoZero eingebaut.



class Sim: 
    def __init__(self, step, stop):
        self.Cnt = 0.0
        self.Step = step     # us 
        self.Stop = stop     # ms maximale Laufzeit


        
class DataCell: 
    def __init__(self, cnt, value):
        self.Cnt = cnt
        self.Value  = value


class ResidueADC:
    def __init__(self, cpu, bits):
        self.Bits = bits  # wieviele bits hat dieses Reste ADC
        self.CPU = cpu
        self.Vbegin = 0.0
        self.Vend = 0.0

    # Liefert die aktuelle Auflösung in uV für diesen Reste ADC
    def GetResolution(self):
        return  self.CPU.Integrator.VrefP / pow(2,self.Bits)
        
    def Reset(self):
        self.Vbegin = 0.0
        self.Vend = 0.0


class Integrator:
    def __init__(self):

        self.RunUpCells = []
        
        self.Vout  = 0.0
        self.Vin   = 1.0
        self.VrefN = -5.0
        self.VrefP = 5.0
        self.SW_Vin = 0
        self.SW_VrefN = 0
        self.SW_VrefP = 0

        self.SW_Reset = 0

        self.ChargingInjection = 0.1 # nF
        self.C = 1.0         # nF
        self.R_Vin   = 200.0 # k
        self.R_VrefN = 100.0 # k
        self.R_VrefP = 100.0 # k
        
        self.t = 0.0
        
        
    def Comp(self):
        if(self.Vout <= 0.0 ):
            return 0
        else:
            return 1

    
    def Calc(self, dt):

        
        Iin = 0.0   # Strom durch Rin
        Iref = 0.0  # Strom durch Rref
        c = self.C *  pow(10, -9)  
        
        if (self.SW_Vin == 0 and self.SW_VrefN == 0 and self.SW_VrefP == 0 ):
            return

        # RunDown
        if (self.SW_Vin == 0 and self.SW_VrefN == 1  ):
            Iin = 0.0
            Iref = self.VrefN / ( self.R_VrefN * pow(10,3) )

        if (self.SW_Vin == 0 and self.SW_VrefP == 1  ):
            Iin = 0.0
            Iref = self.VrefP / ( self.R_VrefP * pow(10,3) )


        # RunUp
        if (self.SW_Vin == 1 and self.SW_VrefN == 1  ): 
            Iin = self.Vin / ( self.R_Vin * pow(10,3))
            Iref = self.VrefN / ( self.R_VrefN * pow(10,3) )
            c = ( self.C+self.ChargingInjection)*pow(10, -9)
            
        if (self.SW_Vin == 1 and self.SW_VrefP == 1 ): 
            Iin = self.Vin / ( self.R_Vin * pow(10,3))
            Iref = self.VrefP / ( self.R_VrefP * pow(10,3) )
            c = (self.C-self.ChargingInjection)*pow(10, -9)
            

        z = -( (1/c) * ( Iin + Iref) * dt )  
        self.Vout =  self.Vout + z 

        
        self.append( dt, self.Vout)


    def append( self, dt, vout ):
        t = self.t + (dt * 1000.0 * 10.0 )
        
        self.RunUpCells.append( DataCell( t, vout))
        self.t =  t

    def Reset( self):
        self.Vout = 0.0
        self.t = 0.0
        self.RunUpCells.clear();
        self.RunUpCells.append( DataCell( self.t, self.Vout))


        
        

    def trace(self):
        return Vout
    
    def toJson(self):
        
        data = []
        
        for item in self.Items:
            data.append ({"Property": item.Parameter, "Value": item.Value, "Operator": item.Operator }) 
        
        return data



#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------


class CPU: 
    def __init__(self):
        
        self.ResidueADC = None

        self.RunUpCycles = 6250    #  Anzahl der Rampen Default
        self.RunUpCnt    = 10000   #  Anzahl der Impulse je Rampe == 1 ms
 
        self.Tick = 0.1            # in us (10Mhz)
        self.RunDownCnt = 0        # Anzahl der Impulse beim down
        self.WaveForm = 16

        self.CntN = 0
        self.CntP = 0
        self.CntAutoZero = 0       # CntP-Cnt-N Offset Kompensation
        self.Vin = 0.0
        self.Resolution = 0.0
        self.RunDown_Sign = 0

        self.X2 = 0.0
        
        self.Vout_Before = 0.0

        self.V1 = 0.0  # calc voltage RunUp
        self.V2 = 0.0  # calc voltage residual ADC
        


        self.Cycles = 0 # ????
        
    def Reset(self):
        self.RunDownCnt = 0 
        self.CntN = 0
        self.CntP = 0
        self.Vin = 0.0
        self.Resolution = 0.0
        self.Tick = 0.1
        self.Integrator.Reset()
        if( self.ResidueADC ):
            self.ResidueADC.Reset()

    def Connect( self, integrator):
        self.Integrator = integrator

    # Mit dem AutoZero den Korrekturwert "self.CntAutoZero" bestimmen
    def AutoZero( self):
               
        vin = self.Integrator.Vin
        
        self.Integrator.Vin = 0.0
        self.RunUp()
        self.CntAutoZero = self.CntP-self.CntN

        self.Integrator.Vin = vin
        self.Reset()


    def RunDown(self):
 
        b = 0

        # Wenn ein Reste ADC installiert ist, holen wir uns nur den Rest aus dem Integrator
        if( self.ResidueADC ):
            self.ResidueADC.Vend = self.Integrator.Vout
            return
        
        self.Vout_Before = self.Integrator.Vout
        
        if( self.Integrator.Comp() == 0 ): 
            self.Integrator.SW_VrefP = 0
            self.Integrator.SW_VrefN = 1      
            self.Integrator.SW_Vin = 0
            b = 0    
            self.RunDown_Sign = 0
        else: 
            self.Integrator.SW_VrefP = 1
            self.Integrator.SW_VrefN = 0 
            self.Integrator.SW_Vin = 0
            b = 1
            self.RunDown_Sign = 1

        while( self.Integrator.Comp() == b ):
            self.Integrator.Calc( self.Tick * pow(10,-6))
            self.RunDownCnt = self.RunDownCnt + 1


 
    
    ## RunUp Version 1
    def RunUp( self):
    
        # Wenn ein Reste ADC installiert ist, merken wir uns den Begin Wert aus dem Integrator
        if( self.ResidueADC ):
            self.ResidueADC.Vbegin = self.Integrator.Vout
        
        t_long = (self.RunUpCnt ) * self.Tick * pow(10,-6)   
        t_short = 0.0   
        
        if( self.WaveForm > 0 ): 
            t_long = (self.RunUpCnt-( self.RunUpCnt / self.WaveForm)) * self.Tick * pow(10,-6)   
            t_short = ( self.RunUpCnt / self.WaveForm) * self.Tick * pow(10,-6)   
            
        for a in range(1,self.RunUpCycles+1):

            if (self.Integrator.Comp() == 1):
                self.Integrator.SW_Vin = 1
                self.Integrator.SW_VrefN = 0
                self.Integrator.SW_VrefP = 1
                self.Integrator.Calc( t_long )      
                if  self.WaveForm > 0: 
                    self.Integrator.SW_VrefN = 1
                    self.Integrator.SW_VrefP = 0          
                    self.Integrator.Calc( t_short )
                self.CntN += 1
            else:
                self.Integrator.SW_Vin = 1
                if  self.WaveForm > 0: 
                    self.Integrator.SW_VrefN = 0
                    self.Integrator.SW_VrefP = 1
                    self.Integrator.Calc( t_short )
                self.Integrator.SW_VrefN = 1
                self.Integrator.SW_VrefP = 0
                self.Integrator.Calc( t_long )                
                self.CntP += 1
             


   

 

    def CalcVin( self):
        
        N = self.CntP  + self.CntN        
        d = (self.RunDownCnt-1)

        # Berechnung siehe: 
        # https://laconga.redclara.net/courses/modulo-instrumentacion/claseMI06/materialesMI6/The_Art_of_Electronics_3rd_ed__Ch13_.pdf

        if( self.ResidueADC ):
            self.V1 = self.Integrator.VrefP * ( ( self.CntN  -self.CntP   ) / N) * (self.Integrator.R_Vin/  self.Integrator.R_VrefN  )
            
            self.V2 = ((self.Integrator.R_Vin* pow(10,3)) * (self.Integrator.C*pow(10,-9)) / ((self.RunUpCnt/10) * pow(10,-6) * N)) * (self.ResidueADC.Vend) 
            #self.V2 = 0.0

            if( self.RunDown_Sign==1 ):
                self.Vin = self.V1 + self.V2
            else:
                self.Vin = (self.V1 + self.V2) * -1
            return

      
      
        if( self.RunDown_Sign==0 ):
            x =  (self.CntP  - self.CntN ) + ( self.RunDownCnt  / self.RunUpCnt )
        else:
             x =  (self.CntP  - self.CntN ) - ( self.RunDownCnt  / self.RunUpCnt )
               
        x1 = (self.Integrator.R_Vin *  self.Integrator.VrefP ) / self.Integrator.R_VrefN 
                
        self.Vin = (x * x1)/(N)

        # **** Gesamtzyklen und Resolution berechnen ****
        TMess = self.Tick * self.RunUpCycles * self.RunUpCycles
        self.Resolution = self.Integrator.VrefP / TMess

        # Resolution = Vref / Messzyklen
        # Messzyklen = 0,1 us * 32 us * (6250 ) = 2.000.000



    def RunUpTime(self):
        return (self.RunUpCnt * self.Tick * pow(10,-6) * self.RunUpCycles) * 1000


        