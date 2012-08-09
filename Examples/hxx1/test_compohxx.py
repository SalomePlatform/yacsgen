#==============================================================================
#  File      : CALCUL_test.py
#  Created   :
#  Author    :
#  Project   : SALOME
#  Copyright : CEA 2005
#==============================================================================
#
# Test du composant CALCUL
#
import SALOME
import salome
salome.salome_init()
print "Test du composant CALCUL genere par hxx2salome"
import hxxcompos_ORB
myCalc = salome.lcc.FindOrLoadComponent("FactoryServer", "CALCUL")
print "10+15 = ",myCalc.add(10,15)
print "10x15 = ",myCalc.mul(10,15)
#print "6!    = ",myCalc.fact(6)
res1,res2 = myCalc.sqr2(12.0)
print "12*12 = ",res1," ",res2
j=1
i1,i2,i3 = myCalc.return_3_int(j)
assert (i1 == j+1),'Erreur dans la fonction return_3_int'
assert (i2 == j+2),'Erreur dans la fonction return_3_int'
assert (i3 == j+3),'Erreur dans la fonction return_3_int'
print 'return_3_int : ',j,' ',i1,' ',i2,' ',i3
print "True && True  = ",myCalc.And(True,True)
print "True && False = ",myCalc.And(True,False)
print "True || False = ",myCalc.Or(True,False)
from math import fabs
assert (fabs(res1-144.0)<1.0e-6 ), 'Erreur dans la fonction myCalc.sqr2 : 12*12 = '+str(res1)
assert ( myCalc.And(True,True)==True ) , 'Erreur dans la fonction And(True,True)'
assert ( myCalc.And(True,False)==False ) , 'Erreur dans la fonction And(True,False)'
assert ( myCalc.Or(True,False)==True ) , 'Erreur dans la fonction Or(True,False)'
print "Fin test hxx2salome/001/A1"
#
#
myTestMed = salome.lcc.FindOrLoadComponent("FactoryServerTM", "TESTMED")
myMedCalc = salome.lcc.FindOrLoadComponent("FactoryServerMC", "MEDCALC")
#
banner = myTestMed.getBanner()
print "Banner = ",banner
assert  banner == "Hello" , 'erreur dans la fonction getBanner() : mauvaise valeur'
#
print "Creation et tests des supports :"
supportName=myTestMed.getSupportName(myTestMed.getSupport())
print "Support name : ",supportName
assert supportName == "SupportOnAll_MED_MAILLE"
#
from libMEDClient import FIELDDOUBLEClient
f_loc=FIELDDOUBLEClient(myTestMed.getVolume(myTestMed.getSupport()))
assert f_loc.getNumberOfValues() == 16 , 'created field has incorrect size'
from math import fabs
assert fabs(f_loc.norm2()-6.39444)<1.0e-5  , 'created field has incorrect norm 2'
##
# CNC bug Medclient  myTestMed.affiche_fieldT(myTestMed.getVolume(myTestMed.getSupport()))
myTestMed.printSupportEntity(myTestMed.getSupport())
myMedCalc.printSupport(myTestMed.getSupport())
myMedCalc.printSupport(myTestMed.getPartialSupport())
f_part=FIELDDOUBLEClient(myTestMed.getVolume(myTestMed.getPartialSupport()))
assert f_part.getNumberOfValues() == 3, 'created field on partial support has incorrect size'
assert fabs(f_part.norm2()-1.15470)<1.0e-5  , 'created field on partial support has incorrect norm 2'
print "Fin test hxx2salome/003/A1"
#
banner = myTestMed.getBanner()
print "Banner = ",banner
assert  banner == "Hello" , 'erreur dans la fonction getBanner() : mauvaise valeur'
#
theMesh= myTestMed.getMesh()
theField = myTestMed.getField()
(theField1,theField2) = myTestMed.create2DoubleField()
#CNC  bug Medclient  myTestMed.affiche_fieldT(theField1)
mynorm=myTestMed.getNormMax(theField)
from math import fabs
assert fabs(mynorm-3.0)<1.0e-10  , 'created field has incorrect norm 1'
print "Norm of the Field : " , mynorm

field1 = myTestMed.getConstFieldDouble( 3.0 , "field1" )
# CNC bug Medclient myTestMed.affiche_fieldT(field1)
print "Creation tableau :"
size=12
myTab = myTestMed.createDoubleTab(size)
myTabInt = myTestMed.createIntVector(size)
myTestMed.printDoubleTab(myTab)
print "Create a matrix"
myTestMed.printMatrix(myTestMed.createMatrix(size,size))
print "Fin test hxx2salome/002/A1"

#
# test of exception mechanism
from SALOME_MED import SUPPORT, MED_NODE, FIELDDOUBLE
test_exception=False
f_cell = myTestMed.getField()
f_node = myTestMed.getFieldOnNode()
try:
        f_wrong=myMedCalc.add(f_cell,f_node)
except SALOME.SALOME_Exception, ex:
        test_exception=True
	print "wrong addition was correctly catched"
	print "Exception is : ",ex

assert test_exception, 'Error in the exception management  : the wrong MED addition was not correctly catched'
print "Fin test hxx2salome/003/A2"

myCoco = salome.lcc.FindOrLoadComponent("FactoryServerI", "ICOCO")
#
liste_champs = myCoco.getInputFieldsNames()
nb_champs=len(liste_champs)
print "Nombre de champs = ",nb_champs
assert  nb_champs == 2 , 'erreur dans le nombre de champs, different de 2!'
#
print "Champ 1 (SourceField) : ",liste_champs[0]
print "Champ 2 (TargetField) : ",liste_champs[1]
assert liste_champs[0] == "SourceField", 'erreur dans le nom du champ 1'
assert liste_champs[1] == "TargetField", 'erreur dans le nom du champ 2'
#
print "Fin test hxx2salome/ICOCO/A1"
myCoco1 = salome.lcc.FindOrLoadComponent("FactoryServerI1", "ICOCO")
myCoco2 = salome.lcc.FindOrLoadComponent("FactoryServerI2", "ICOCO")
#
myCoco1.initialize()
m=myCoco1.getInputFieldTemplate("TargetField")
myCoco1.solve()  #to test with 5.1.5
f=myCoco1.getOutputField("SourceField")
myCoco2.printField(f)
#
print "##################################"
print "Fin test hxx2salome/ICOCO/A2"
