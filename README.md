# Multi-Slope-ADC-Jupyter
Simulation eines Multi-Slope ADC

Um die Funktionsweise eines Multi-Slope ADC besser zu verstehen, habe ich eine Simulation mit Jupyter Lab in Python geschrieben. 
Die Version ist noch etwas rudimentär, jedoch lassen sich schon unterschiedliche Wave-Formen und unterschiedliche Fehlerquellen simulieren. 
Mit der Simulation kann gezeigt werden, welche Fehlerquellen ein lineares oder nicht lineares Verhalten haben.


# Linearität

## Ideal-Fall
Wenn wir die Eingangswiderstände (Rin, Rref+ und Rref-) und die Vref Spannungen als ideal annehmen, bekommen wir folgende Anweichung.

integrator.VrefN = -7.04480
integrator.VrefP = 7.04480
integrator.ChargingInjection = 0.000

integrator.R_Vin   = 50.0 # k
integrator.R_VrefN = 50.0 # k
integrator.R_VrefP = 50.0 # k


![Mein Bild](doc/images/Abweichung_RunDown_Ideal.png)



## Real-Fall
Da wir in der Realität jedoch Abweichungen in den Widerständen und in der Vref-Spannung bekommen, erhalten wir eine lineare Abweichung. Selbst kleine unterschiede in den Widerständen-Array führen zur eine linearen Abweichung.

Beispiel:

integrator.VrefN = -7.04580
integrator.VrefP = 7.04480
integrator.ChargingInjection = 0.000

integrator.R_Vin   = 50.0 # k
integrator.R_VrefN = 50.01 # k
integrator.R_VrefP = 50.00 # k

![Mein Bild](doc/images/Abweichung_RunDown_real.png)
