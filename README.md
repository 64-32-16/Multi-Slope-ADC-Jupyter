# Multi-Slope-ADC-Jupyter
Simulation eines Multi-Slope ADC (20 Bit)

Um die Funktionsweise eines Multi-Slope ADC besser zu verstehen, habe ich eine Simulation mit Jupyter Lab in Python geschrieben. 
Die Version ist noch etwas rudimentär, jedoch lassen sich schon unterschiedliche Wave-Formen und unterschiedliche Fehlerquellen simulieren. 
Mit der Simulation kann gezeigt werden, welche Fehlerquellen ein lineares oder nicht lineares Verhalten haben.

Die Simulation unterscheidet grundsätzlich zwei Formen von der RunDown-Phase. Einmal eine Zeitmessung nach der RunUp-Phase oder eine Restwert-Messung über einen Residual-ADC nach der RunUp-Phase.

Eine gute Einführung in das Thema [Multi-Slope ADC](https://en.wikipedia.org/wiki/Integrating_ADC) gibt es auf Wikipedia

# Linearität
In der Simulation wird für die Betrachtung der Linearität eine Eingangsspannung Vin von -5.0V bis +5.0V in 0.5 V Schritten durchlaufen.


## Ideal-Fall mit RunDown (Zeitmessung)
Wenn wir die Eingangswiderstände (Rin, Rref+ und Rref-) und die Vref Spannungen als ideal annehmen, bekommen wir folgende Anweichung.

integrator.VrefN = -7.04480 <br>
integrator.VrefP = 7.04480 <br>
integrator.ChargingInjection = 0.000 <br>

integrator.R_Vin   = 50.0 # k <br>
integrator.R_VrefN = 50.0 # k <br>
integrator.R_VrefP = 50.0 # k <br>


![Mein Bild](doc/images/Abweichung_RunDown_Ideal.png)



## Real-Fall mit RunDown (Zeitmessung)
Da wir in der Realität jedoch Abweichungen in dem Widerständs-Array und in der +/-Vref-Spannung bekommen, erhalten wir eine lineare Abweichung. Selbst kleine unterschiede in den Widerständs-Array und +/-Vref-Spannungen führen zur einer linearen Abweichung.

Beispiel:

**integrator.VrefN = -7.04580** <br>
integrator.VrefP = 7.04480 <br>
integrator.ChargingInjection = 0.000 <br>

integrator.R_Vin   = 50.0 # k <br>
**integrator.R_VrefN = 50.01 # k** <br>
integrator.R_VrefP = 50.00 # k <br>

![Mein Bild](doc/images/Abweichung_RunDown_real.png)

## Mögliche Lösungen 
### 1. Präzise Widerstände mit geringer Toleranz verwenden

Der einfachste Ansatz ist, hochwertige Widerstände mit geringen Toleranzen (z. B. 0,01 % oder besser) und niedrigem Temperaturkoeffizienten (< 10 ppm/∘C) zu verwenden. Dies reduziert die Fehlanpassung auf ein Minimum.

Vorteil: Einfach und kostengünstig bei geringer Fehlanpassung. <br>
Nachteil: Physische Grenzen durch Bauteiltoleranzen. <br>

### 2. Präzise Spannungsreferenz z.B. LM399

Auch hier muß bei der Erzeugung der negativen Spannung -Vref ein möglichs präzises Widerstands-Array verwendet werden.

### 3. Digitale Kalibrierung (empfohlen bei hochgenauen ADCs)

Digitale Kalibrierung bietet eine flexible Möglichkeit, die Fehlanpassung der Eingangswiderstände zu korrigieren. Dabei wird das Verhalten des Systems gemessen und die Abweichungen durch Software kompensiert.

Vorgehen:
Messung des Fehlers:

Einspeisen einer bekannten Spannung (𝑉cal) mit positivem und negativem Eingang.
Den systematischen Unterschied zwischen den gemessenen und relaen Wert ermitteln und gespeichert.

## Real-Fall mit RunDown (Zeitmessung) und Kalibierung
