#!/usr/bin/env python
###############################################################
#Developed on Python 2.7.8
#Author : Kiran Kariyannavar (nxp50069)
###############################################################

###############################################################
import csv
import re
from collections import defaultdict
###############################################################

p = re.compile('\[.*\]')

#########################################################################################################
tpr_manual="sw_mtp"  #Name of TPR which is manually done and to be excluded for information extraction
#########################################################################################################

##############################################################
########### READ ANALOG PORT LIST  ###########################
##############################################################
ifile  = open('analog_port_list.csv', "rb")
reader = csv.reader(ifile,delimiter=',')
##############################################################

##############################################################
# Default column numbers in the analog port list
digital_signal_name_col_num = 0
analog_signal_name_col_num  = 1
analog_shell_name_col_num  = 14
signal_direction_col_num    = 3
tp_isolation_col_num        = 4
toggle_info_col_num         = 5
tpr_names_col_num           = 11
tpr_order_col_num           = 12
##############################################################

###############################################################################################################
# Ouput Files
f = open("tpr_order.txt", 'w')              #File containing TPR order
g = open("isolation.txt", 'w')              #File containing scan isolation information
e = open("ERRORS.txt", 'w')                 #File containing different errors in the port list
aif = open("analog_top_inst.inc.v", 'w')    #File containing the analog top module instantiation in core
dif = open("digital_top_inst.inc.v", 'w')   #File containing the digital top module instantiation in core
adif_wires = open("ana_dig_wires_inst.inc.v", 'w')   #File containing the digital top module instantiation in core

tpr_muxes_file = open("tpr_muxes_signal_list", 'w')              #File containing signal lists of AO domain for TPR muxes module creation

###############################################################################################################

##############################################################
######## EXTRACT INFO FROM CSV     ###########################
##############################################################
d = defaultdict(list)
def extract_info () :
    total_dynamic_signals = 0
    rownum = 0
    for row in reader:
        # Save header row.
        if rownum == 0:
            header = row
            colnum = 0
            for col in row :
                col = col.upper()
                col = col.strip()
                if col == "TPR_ORDER" :
                    tpr_order_col_num = colnum
                if col == "TP_ISOLATION" :
                    tp_isolation_col_num = colnum
                if col == "ANALOG_TOP_PORT_NAME" :
                    analog_signal_name_col_num = colnum
                if col == "DIRECTION" :
                    signal_direction_col_num = colnum
                if col == "SCAN_ISOLATION" :
                    toggle_info_col_num = colnum
                if col == "TPR_NAME" :
                    tpr_names_col_num = colnum
                if col == "POWER_DOMAIN" :
                    power_domain_col_num = colnum
                if col == "DYNAMIC_GROUP" :
                    dynamic_col_num = colnum
                if col == "ANALOG_SHELL_PORT_NAME" :
                    analog_shell_name_col_num = colnum
                colnum += 1
        else :
           colnum = 0

#Check if any signals without power domain
           if row[power_domain_col_num] == "" and row[analog_signal_name_col_num] != "" and row[tp_isolation_col_num] != "power" and row[tp_isolation_col_num] != "analog"   :
               print "PD: %s signal has no power domain information " % (row[analog_signal_name_col_num])

#Check if any signals without tpr association
           if row[tpr_names_col_num] == "" and row[analog_signal_name_col_num] != ""   :
               print "TPR: %s signal has no associated tpr " % (row[analog_signal_name_col_num])
           if row[analog_signal_name_col_num] == "" and row[digital_signal_name_col_num] != "" :
               print "ANA1: This %s signal has no equivalent analog signal " % (row[digital_signal_name_col_num])
           if (row[tp_isolation_col_num].upper() == "DYNAMIC" or row[tp_isolation_col_num].upper() == "TMUX" ) and row[dynamic_col_num] == "" :
               print "ERROR: DYN1: %s signal is defined dynamic but does not belong to any dynamic group " % (row[analog_signal_name_col_num])

           if (row[tp_isolation_col_num].upper() == "DYNAMIC" or row[tp_isolation_col_num].upper() == "TMUX" ) and row[dynamic_col_num] != "" :

               total_dynamic_signals +=1
               group =   row[dynamic_col_num].split(":" )
               for i in group:
                    if row[signal_direction_col_num].upper() == "OUTPUT":
                        coreport =row[analog_signal_name_col_num]+"_outp_dyn"
                        ttype = "OUT"
                    else :
                        coreport =row[analog_signal_name_col_num]+"_inp_dyn"
                        ttype = "IN"
                    mode = i.strip()
                    tmux_input = mode + '\t' + "SIGNAL" + '\t' + coreport + '\t' + ttype + '\t' + "TAPMODE"
                    d[mode].append(tmux_input)
               #print coreport
               aif.write('.%s(%s\t) , \n' % (coreport.ljust(40),coreport.ljust(40)  ))

           if row[analog_signal_name_col_num] != ""  :
# Write Digital Top and Analog Top Instantiation
              analog_port = row[analog_signal_name_col_num].strip()
              bus = row[analog_signal_name_col_num].strip()
              match = re.search(r'\[.*\]', bus)
              if match :
                  bus_width = match.group()
              else :
                  bus_width = "\t"

              analog_port = re.sub('\[.*',"",analog_port)
              analog_shell_port = row[analog_shell_name_col_num].strip()
              analog_shell_port = re.sub('\[.*',"",analog_shell_port)
              digital_port = row[digital_signal_name_col_num].strip()

              if digital_port == "":
                  adif_wires.write('wire\t%s\t%s\t;\n' % (bus_width,analog_port.ljust(30)))
                  dif.write('.%s(%s\t) ,// TBC !!!  \n' % (analog_port.ljust(40),analog_port.ljust(40)  ))
              else :
                  adif_wires.write('wire\t%s\t%s\t;\n' % (bus_width,digital_port.ljust(30)))
                  dif.write('.%s(%s\t) , \n' % (digital_port.ljust(40),digital_port.ljust(40)  ))

              if row[tpr_names_col_num] !="sw_mtp":
                  aif.write('.%s(%s\t) , \n' % (analog_port.ljust(40),digital_port.ljust(40)  ))
              else :
#                   print analog_shell_port
                   aif.write('.%s(%s\t) , \n' % (analog_shell_port.ljust(40),digital_port.ljust(40)  ))



           for col in row:
               if colnum == tpr_order_col_num and col != "" and col !="sw_mtp"  :
                   f.write('%s ' % (col))
               if col == "clamp_zero" and row[tpr_names_col_num] !="sw_mtp"  :
                   g.write ('%s;%s\n' % (row[analog_signal_name_col_num],row[tpr_names_col_num]))
               if (colnum == tpr_names_col_num) and ((col == "ao_func" or col == "ao_trim"  ) and (row[analog_signal_name_col_num] !="" and row[tp_isolation_col_num] !="bypass"
                   and row[tp_isolation_col_num] !="analog"  and row[tp_isolation_col_num] !="tmux"   )) :
                   tpr_muxes_file.write ('%s;%s\n' % (row[analog_signal_name_col_num],row[signal_direction_col_num]))
               colnum += 1

        rownum += 1
    #print  "total dynamic signals : %i " % (total_dynamic_signals)
    #print d.items()
    f.close()
    g.close()
    e.close()
    aif.close()
    tpr_muxes_file.close()
    dif.close()
    adif_wires.close()
##############################################################
extract_info()


#Prepare the tmux file for dynamic groups

t = open("tmux.txt", 'w')
d_g_c = 0

with open("dyn_io.txt", "r") as _f:
    myfile = _f.readlines()
myline = myfile[0]
io_list = myline.split(":")

no_of_dyn_sup = 4

for i in d.keys():
    io_c = 0
    if len(d[i]) > no_of_dyn_sup :
        print "This %s group has more dynamic signals (%s)than supported (%s) : " % (i,len(d[i]),no_of_dyn_sup)
    #else :
          #print "This %s group has %s dynamic signals " % (i,len(d[i]))
    for j in d[i]:
        j=j.replace("SIGNAL",io_list[io_c])
        j=j.replace("TAPMODE","-" )
        t.write('%s\t  \n' % (j))
        io_c += 1
        d_g_c += 1

t.close()
#print d_g_c


ifile.close()







# Reference

