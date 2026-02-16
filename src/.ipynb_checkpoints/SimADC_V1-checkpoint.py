






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
    def __init__(self, cpu, bits, inputVolt):
        self.Bits = bits  # wieviele bits hat dieses Reste ADC
        self.InputVolt = inputVolt # in Volt
        self.CPU = cpu
        self.Vbegin = 0.0
        self.Vend = 0.0
        self.Resolution = self.InputVolt/pow(2,self.Bits)

    def calc( self, volt):
        x = round( volt/ self.Resolution, 0)	
        return (x * self.Resolution)


    # Liefert die aktuelle Auflösung in uV für diesen Reste ADC
    def GetResolution(self):
        return  self.CPU.Integrator.VrefP / pow(2,self.Bits)
        
    def Reset(self):
        self.Vbegin = 0.0
        self.Vend = 0.0


class ADCCalibration:
    def __init__(self, calibration_points):
        """
        Initialisiert die Kalibrierung mit mehreren Punkten.

        :param calibration_points: Liste von (V_adc, V_in)-Paaren, sortiert nach V_adc
        """
        if len(calibration_points) < 2:
            raise ValueError("Es müssen mindestens zwei Kalibrierungspunkte angegeben werden.")
        
        # Punkte nach V_adc sortieren
        self.calibration_points = sorted(calibration_points, key=lambda p: p[0])

    def calibrate(self, v_adc):
        """
        Kalibriert den ADC-Wert basierend auf den Kalibrierungspunkten.

        :param v_adc: Gemessener ADC-Wert
        :return: Kalibrierte Eingangsspannung
        """
        # Suche den Bereich, in den der ADC-Wert fällt
        for i in range(len(self.calibration_points) - 1):
            adc1, vin1 = self.calibration_points[i]
            adc2, vin2 = self.calibration_points[i + 1]

            if adc1 <= v_adc <= adc2:
                # Berechne Steigung und Achsenabschnitt für diesen Bereich
                m = (vin2 - vin1) / (adc2 - adc1)
                b = vin1 - m * adc1
                return m * v_adc + b
        
        # Fehler, falls der Wert außerhalb der Kalibrierungsbereiche liegt
        raise ValueError("ADC-Wert liegt außerhalb der Kalibrierungsbereiche.")



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
        """
        Parasitärer Effekt der Schalter (Ladeinjektion):
        Modelliert als direkte Ladungsinjektion, nicht als Kapazitätsänderung.
        """
        if self.SW_Vin == 0 and self.SW_VrefN == 0 and self.SW_VrefP == 0:
            self.append(dt, self.Vout)
            return

        C = self.C * 1e-9  # Integratorkapazität in Farad
        q_inj = self.ChargingInjection * 1e-12  # Ladeinjektion in Coulomb
        Iin = 0.0
        Iref = 0.0

        if self.SW_Vin == 1:
            Iin = self.Vin / (self.R_Vin * 1e3)

        if self.SW_VrefN == 1:
            Iref += self.VrefN / (self.R_VrefN * 1e3)

        if self.SW_VrefP == 1:
            Iref += self.VrefP / (self.R_VrefP * 1e3)

        q_total = -(Iin + Iref) * dt  # Gesamtladung

        # Ladeinjektion berücksichtigen, nur wenn genau ein Schalter aktiv ist
        if self.SW_VrefN == 1 and self.SW_VrefP == 0:
            q_total += q_inj
        elif self.SW_VrefP == 1 and self.SW_VrefN == 0:
            q_total -= q_inj

        delta_v = q_total / C
        self.Vout += delta_v
        self.append(dt, self.Vout)


    def append( self, dt, vout ):
        t = self.t + (dt * 1000.0 * 10.0 )
        
        self.RunUpCells.append( DataCell( t, vout))
        self.t =  t

    def Reset( self):
        self.Vout = 0.0
        self.t = 0.0
        self.RunUpCells.clear()
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
        self.VAutoZero = 0.0       # CntP-Cnt-N Offset Kompensation
        self.Vin = 0.0
        self.Resolution = 0.0
        self.RunDown_Sign = 0

        self.X2 = 0.0
        
        self.Vout_Before = 0.0

        self.V1 = 0.0  # calc voltage RunUp
        self.V2 = 0.0  # calc voltage residual ADC
        
        self.Calibration = None


        self.Cycles = 0 # ????
        
    def Reset(self):
        self.RunDownCnt = 0 
        self.CntN = 0
        self.CntP = 0
        self.Vin = 0.0
        self.Resolution = 0.0
        self.Tick = 0.2
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
        self.RunDown()
        self.CalcVin()
        self.VAutoZero = self.Vin

        self.Integrator.Vin = vin
        self.Reset()


    def RunDown(self):
 
        b = 0

        # Wenn ein Reste ADC installiert ist, holen wir uns nur den Rest aus dem Integrator
        # ToDo Anzahl der Bits beim Reste ADC beachten
        if( self.ResidueADC ):
            self.ResidueADC.Vend = self.ResidueADC.calc(self.Integrator.Vout)
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
            t_long = (self.RunUpCnt  ) * self.Tick * pow(10,-6)   
            t_short = (  self.WaveForm) * self.Tick * pow(10,-6)   
            
        for a in range(1,self.RunUpCycles+1):

            
            if (self.Integrator.Comp() == 1):
                self.Integrator.SW_Vin = 1

                if  self.WaveForm > 0: 
                    self.Integrator.SW_VrefN = 1
                    self.Integrator.SW_VrefP = 0          
                    self.Integrator.Calc( t_short  )
                
                self.Integrator.SW_VrefN = 0
                self.Integrator.SW_VrefP = 1
                self.Integrator.Calc( t_long )      


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
                         

    ## RunUp Version 2
    ## Version kommt aus dem Parent
    def RunUpV2( self):
    
        # Wenn ein Reste ADC installiert ist, merken wir uns den Begin Wert aus dem Integrator
        if( self.ResidueADC ):
            self.ResidueADC.Vbegin = self.Integrator.Vout
        
        t_long = (self.RunUpCnt ) * self.Tick * pow(10,-6)   
        t_short = 0.0   
        if( self.WaveForm > 0 ): 
            t_short = (  self.WaveForm) * self.Tick * pow(10,-6)   
            
        for a in range(1,self.RunUpCycles+1):

            # Phase 1 Vin == 1
            # Integration
            self.Integrator.SW_Vin = 1
            self.Integrator.SW_VrefN = 0
            self.Integrator.SW_VrefP = 0   
            self.Integrator.Calc( t_long ) 
            
            self.Integrator.SW_Vin = 0
           
            # KOMPENSATION
            self.Integrator.SW_VrefN = 0
            self.Integrator.SW_VrefP = 0
            self.Integrator.Calc( t_short ) 

            # Deintegration
            if (self.Integrator.Comp() == 1):
                
                self.Integrator.SW_VrefN = 0
                self.Integrator.SW_VrefP = 1
                self.Integrator.Calc( t_long )      

 
                self.CntN += 1
            else:

                self.Integrator.SW_VrefN = 1
                self.Integrator.SW_VrefP = 0
                self.Integrator.Calc( t_long )   
                
               
                        
                self.CntP += 1
  
            # Kompensation
            self.Integrator.SW_VrefN = 1
            self.Integrator.SW_VrefP = 1
            self.Integrator.Calc( t_short )   

 

    def CalcVin( self):
        

        N = self.CntP  + self.CntN        # Gesamt Count   
        Np = self.CntN    
        Nn = self.CntP    
     

        #d = (self.RunDownCnt )


        x1 = (Np-Nn)
        x2 = (Np + Nn ) 
        self.V1 = self.Integrator.VrefN *  (x1 / x2 ) * (2)
        
        self.V2 = ((self.Integrator.R_Vin* pow(10,3)) * (self.Integrator.C*pow(10,-9)  * (self.ResidueADC.Vend) ) /  ((self.RunUpCnt) * pow(10,-6)/10 * N))
        self.V2 = self.V2/2.0
        
        self.Vin = self.V1 - (self.V2)
        
        if( self.Calibration):
            self.Vin = self.Calibration.calibrate( self.Vin ) 
        return




        # ###### Berechnung mit Residual ADC siehe: 
        # https://laconga.redclara.net/courses/modulo-instrumentacion/claseMI06/materialesMI6/The_Art_of_Electronics_3rd_ed__Ch13_.pdf

        if( self.ResidueADC ):
            self.V1 = self.Integrator.VrefP * ( ( self.CntN  -self.CntP   ) / N) * (self.Integrator.R_Vin/  self.Integrator.R_VrefN  )
            
            self.V2 = ((self.Integrator.R_Vin* pow(10,3)) * (self.Integrator.C*pow(10,-9)) / ((self.RunUpCnt/10) * pow(10,-6) * N)) * (self.ResidueADC.Vend) 
            #self.V2 = 0.0

            if( self.RunDown_Sign==1 ):
                self.Vin = self.V1 + self.V2

            else:
                self.Vin = (self.V1 + self.V2) * -1.0


            if( self.Calibration):
                self.Vin = self.Calibration.calibrate( self.Vin ) 
            
            return

      
        # ###### Berechnung mit RunDown-Phase: 
        # https://laconga.redclara.net/courses/modulo-instrumentacion/claseMI06/materialesMI6/The_Art_of_Electronics_3rd_ed__Ch13_.pdf
      
        if( self.RunDown_Sign==0 ):
            x =  ( Np - Nn ) + ( self.RunDownCnt  / self.RunUpCnt )
            #self.VAutoZero = self.VAutoZero * -1.0
        else:
             x =  (Np  - Nn ) - ( self.RunDownCnt  / self.RunUpCnt )
             
             

        # Wenn Rin und Rvref identisch sind, kann dieser Term vereinfacht werden.       
        x1 = (self.Integrator.R_Vin *  self.Integrator.VrefP ) / self.Integrator.R_VrefN 
                
        self.Vin = ( (x * x1)/(N) ) 

        if( self.Calibration):
            self.Vin = self.Calibration.calibrate( self.Vin ) 

        # **** Gesamtzyklen und Resolution berechnen ****
        TMess = self.RunUpCycles * N
        self.Resolution = self.Integrator.VrefP / TMess

        # Resolution = Vref / Messzyklen
        # Messzyklen = 0,1 us * 32 us * (6250 ) = 2.000.000



    def RunUpTime(self):
        return (self.RunUpCnt * self.Tick * pow(10,-6) * self.RunUpCycles) * 1000



