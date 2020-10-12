"""
-*- coding: utf-8 -*-
Rutina de la noche
funciones
Emmanuel C., Angel Daniel A.
2020 I
"""
import sys
import time
import json
import os
import glob
import datetime
import smtplib 
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager

from PIL import Image
from xlrd import open_workbook
from xlwt import Borders, XFStyle, Formula, Font
from xlutils.copy import copy
from mpl_toolkits.basemap import Basemap
from funest import SGC_Performance
from obspy import UTCDateTime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from PyPDF2 import PdfFileWriter, PdfFileReader

def edit_fun(path, f):                #crear txt a partir del .json
    #el valor f es la fecha YYYYMMDD
    
    #parametros de entrada
    year,mes,dia = f[0:4],f[4:6],f[6:8]
    rsnc_stations = []

    with open(f"{path}/jsons/datasta{f}.json", "r") as json_file:
        data = json.load(json_file)

    #FUNCION PARA CREAR Y EDITAR LOS ARCHIVOS func{admin}.txt
    def txt(sta_f, admin,f):

        func = open(f"{path}/txt/func{admin}{f}.txt","w")
        sta_fuera = sta_f
        sta_com,v = [],[]

        for result in data:

            if result["administrador"]==admin and result["estacion"] not in sta_fuera:
                if (str(result["estacion"])+str(result["localizacion"])) not in sta_com: 
                    if float(result["valor"]) > 100:
                        valor=100
                    else:
                        valor=float(result["valor"])
                    sta_com.append(str(result["estacion"])+str(result["localizacion"]))
                    v.append([result["estacion"],result["longitud"],result["latitud"],result["net"],valor,result["#Gaps"],result["localizacion"]])
                else: continue

        if admin != "INTER":
            v2 = sorted(v)
            es = ""
            for e in range(len(v)):
                long = v2[e][1]
                lat = v2[e][2]
                valor = v2[e][4]
                estacion = v2[e][0]
                net = v2[e][3]
                gaps = v2[e][5]
                loc = v2[e][6]
                es += str(long).ljust(11," ")+", "+str(lat).ljust(10," ")+","+str(valor).rjust(7," ")+",  "+str(gaps).rjust(3," ")+", "+str(estacion).ljust(5," ")+", "+str(loc)+"\n"

            func.write(es)
            func.close()
 
        else:
            es = ""
            for e in range(len(v)):
                long = v[e][1]
                lat = v[e][2]
                valor = v[e][4]
                estacion = v[e][0]
                loc = v[e][6]
                gaps = v[e][5]
                net = v[e][3]
                es += str(long).ljust(11," ")+", "+str(lat).ljust(10," ")+","+str(valor).rjust(7," ")+",  "+str(gaps).rjust(3," ")+", "+str(estacion).ljust(5," ")+", "+str(net)+"\n"
            func.write(es)
            func.close()


    """
    RSNC
    """
    sta_fuera = ["TABC","MARO","SOTO","CONO", "BOG","CVER","PIRM","TAPM","ACH1","ACH2","ACH3","ACH4","ACH5","ACH6","ACH7"]
    txt(sta_fuera,"RSNC",f)
    """
    RNAC
    """
    sta_fuera = ["CMOC1","CMOC2","CMOC3","CMOC4","CMOC5","CBETA","CGARZ","CIBA3","CNEIV","CPLAT","CPOP2","CPRAD","CSAGU","CSAL1"]
    txt(sta_fuera,"RNAC",f)
    """
    SUB REDES
    """
    sta_fuera =["DRL01","DRL02","DRL03","DRL04","DRL05","DRL06"]
    txt(sta_fuera,"SUB",f)
    """
    SUB RED DRUMMOND
    """
    sta_fuera =["CVER","TABC"]
    txt(sta_fuera,"DRL",f)
    """
    INTERNACIONALES
    """
    sta_fuera = ["CONO","MARO","SOTO"]
    txt(sta_fuera,"INTER",f)

def histograma(path, network,f):      #crear histogramas  
    #valor de f es un str() con la fecha YYYYMMDD
    
    font_path=f"{path}/fonts"
    font_prop1 = font_manager.FontProperties(fname=font_path+"/Aller/Aller_Bd.ttf", size= 15)
    font_prop2 = font_manager.FontProperties(fname=font_path+"/Aller/Aller_Rg.ttf", size=9)
    font_prop3 = font_manager.FontProperties(fname=font_path+"/Aller/Aller_Bd.ttf", size= 10)
    
    
    func_ = open(f"{path}/txt/func{network}{f}.txt","r").readlines()
    
    if network == "RSNC": tit = "PORCENTAJE FUNCIONAMIENTO RSNC \n"
    if network == "SUB": tit = "PORCENTAJE FUNCIONAMIENTO SUB-REDES \n"
    if network == "DRL": tit = "PORCENTAJE FUNCIONAMIENTO DRUMMOND \n"
    if network == "INTER": tit = "PORCENTAJE FUNCIONAMIENTO INTERNACIONAL \n"
    if network == "RNAC": tit = "PORCENTAJE FUNCIONAMIENTO RNAC \n"
    estaciones1,porc1,numgap1 = [],[],[]
    
    for e in func_:
        long,lat,valor,gaps,est,cod = e.split(",")
        esta= est.ljust(5," ")
        estaciones1.append(f"{esta}{cod}")
        porc1.append(float(valor))
        numgap1.append(gaps)
        
    estaciones = estaciones1[::-1]
    porc = porc1[::-1]
    numgap = numgap1[::-1]
    fig= plt.figure(figsize=(8, 12), dpi=300, facecolor="#898b8d")
    
    im = Image.open(f'{path}/logos/sgc_logo.png')
    im.thumbnail((759,181), Image.ANTIALIAS)
    width, height= im.size[0],im.size[1]
    im = np.array(im).astype(np.float) / 255
    fig.figimage(im, fig.bbox.xmax - width -60, fig.bbox.ymax - height-20)
    
    # im2 = Image.open(f'{path}/logos/logo_MIN.png')
    # im2.thumbnail((1059,481), Image.ANTIALIAS)
    # width2, height2= im2.size[0],im2.size[1]
    # im2 = np.array(im2).astype(np.float) / 255
    # fig.figimage(im2, fig.bbox.xmax - width2 -60, height2)

    index = np.arange(len(estaciones))
    
    plt.barh(index, porc, align="edge", color= "#8ca448")
    plt.xticks(np.arange(0,101,10), fontproperties=font_prop2)
    plt.xlabel("%", fontsize=10,fontproperties=font_prop2)
    plt.yticks(index, estaciones, fontsize=10, rotation=0, fontproperties=font_prop2)
    plt.ylim(0,len(estaciones))
    plt.xlim(0,100)

    plt.title(f"{tit} {f[:4]} {f[4:6]} {f[-2:]}", fontproperties=font_prop1)
    plt.grid()
    plt.text(100,len(func_),"#Gaps", fontproperties=font_prop3)
    plt.text(-10,len(func_),"Estacion", fontproperties=font_prop3)
    for ie, v in enumerate(numgap): 
        plt.text(100, ie+0.1 , str(v), fontproperties=font_prop2)
        
    plt.savefig(f"{path}/histogramas/hist_{network}_{f}.pdf", format="pdf", quality=100)
    time.sleep(3) #para darle tiempo de guardar
    return f"{path}/histogramas/hist_{network}_{f}.pdf"
    #~ os.system(f"evince -f {path}/histogramas/hist_{network}_{f}.pdf")

def info_excel(path, f):              #crear excel 
    #el valor de f es la fecha YYYYMMDD "20191207"
    
    year,mes,dia = f[0:4],f[4:6],f[6:8]

    rb = open_workbook(f"{path}/excel/INFORMENOCHE2.xls",formatting_info=True)
    wb = copy(rb)
    hoja = wb.get_sheet(0)

    style = XFStyle()
    style2 = XFStyle()

    fnt = Font()
    fnt.bold = True

    borders = Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1

    style.borders = borders
    style2.borders = borders
    style2.font = fnt

    fil1 = 8        # fila-1 de inicio estaciones RSNC
    fil11 = fil1    # fila actual de RSNC
    ave1 = 0        # fila-1 promedio estaciones RSNC
    col = 4         # columna-1 estaciones RSNC
    fil2 = 10       # fila-1 de inicio estaciones SUB-REDES
    col2 = 19       # columna-1 de inicio estaciones SUB-REDES
    ave2 = 0        # fila-1 promedio estaciones SUB-REDES
    fildr = 35      # fila-1 de inicio estaciones DRUMMOND
    coldr = 19      # columna-1 de inicio estaciones DRUMMOND
    avedr = 0       # fila-1 promedio estaciones DRUMMOND
    fil3 = 9        # fila-1 de inicio estaciones INTERNACIONALES
    col3 = 32       # columna-1 destaciones INTERNACIONALES

    meses = ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO","JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]
    hoja.write(2,2,"%s DE %s DE %s"%(dia,meses[int(mes)-1], year),style=style2)

    func_rsnc = open(f"{path}/txt/funcRSNC{f}.txt","r").readlines()
    func_sub = open(f"{path}/txt/funcSUB{f}.txt","r").readlines()
    func_drl = open(f"{path}/txt/funcDRL{f}.txt","r").readlines()
    func_int = open(f"{path}/txt/funcINTER{f}.txt","r").readlines()


    """
    RSNC
    """
    for i in func_rsnc:
        long,lat,valor,gaps,est,cod = i.split(",")
        hoja.write(fil1,col,float(valor),style=style)
        
        if float(valor) > 0:
            hoja.write(fil1,col-1,"OK",style=style)    #para agregar en ADQUISICION "OK"  080819
            hoja.write(fil1,col-2,"OK",style=style)
        if float(valor) < 0.5:
            hoja.write(fil1,col-2,"X",style=style)    #para agregar en ESTADO D LA ESTACION  "X" 080819
            hoja.write(fil1,col-1,"X",style=style)
        hoja.write(fil1,col-3,est,style=style)
        if est == "CAP2" or est == "CUM":
            hoja.write(fil1,col+9,"CASETA",style=style)
        else: hoja.write(fil1,col+9,"BUNKER",style=style)
        fil1 = fil1+1
    ave1 = fil1
    hoja.write(ave1,col,Formula("AVERAGE(E%s:E%s)"%(fil11+1,ave1)),style=style2)

    """
    SUB
    """
    fil22 = fil2
    for i in func_sub:
        long,lat,valor,gaps,est,cod = i.split(",")
        hoja.write(fil2,col2,float(valor),style=style)
        hoja.write(fil2,col2-3,est,style=style)
        fil2 = fil2+1
    ave2=fil2
    hoja.write(ave2,col2,Formula("AVERAGE(T%s:T%s)"%(fil22+1,ave2)),style=style2)

    """
    SUB RED DRUMMOND
    """
    fildr2 = fildr
    for i in func_drl:
        long,lat,valor,gaps,est,cod = i.split(",")
        hoja.write(fildr,coldr,float(valor),style=style)
        hoja.write(fildr,coldr-3,est,style=style)
        fildr = fildr+1
    avedr = fildr
    hoja.write(avedr,coldr,Formula("AVERAGE(T%s:T%s)"%(fildr2+1,avedr)),style=style2)



    """
    INTERNACIONALES
    """
    for i in func_int:
        long,lat,valor,gaps,est,loc = i.split(",")
        loc1 = loc[0:3]
        hoja.write(fil3,col3,float(valor),style=style)
        if float(valor) > 0:
            hoja.write(fil3,col3+1,"Llegando",style=style)    #para agregar si esta  o "Llegando" 080819
        if float(valor) == 0:
            hoja.write(fil3,col3+1,"Por fuera",style=style)    #para agregar si esta "Por fuera"  080819
        hoja.write(fil3,col3-1,est,style=style)
        hoja.write(fil3,col3-2,loc1,style=style)
        fil3 = fil3 + 1

    wb.save(f'{path}/excel/INFORMENOCHE2.xls') 
    os.system(f"libreoffice {path}/excel/INFORMENOCHE2.xls &")

    os.system(f"libreoffice {path}/excel/FUNDIARIO_GENE.xls")

def func_map(path,network, date):    #crear mapa
    #el valor de network es la fecha YYYYMMDD "20191207"
    
    font_path=f"{path}/fonts"
    font_prop1 = font_manager.FontProperties(fname=font_path+"/Aller/Aller_Bd.ttf")
    font_prop2 = font_manager.FontProperties(fname=font_path+"/Aller/Aller_Bd.ttf", size=15)
    font_prop3 = font_manager.FontProperties(fname=font_path+"/Aller/Aller_Bd.ttf", size= 10)
       
    latitud=[]
    longitud=[]
    percentage=[]
    name=[]
    date_to_map= date[:4]+' '+ date[4:6]+ ' '+ date[-2:] 
    
    filename= f'{path}/txt/func{network}{date}.txt'
    f= open(filename, 'r')
    contents_as_list= f.read().splitlines()

    for line in contents_as_list:
        line_split = line.split(',')
        latitud.append(float(line_split[0]))
        longitud.append(float(line_split[1]))
        percentage.append(float(line_split[2]))
        name.append(str(line_split[4]).strip())

    fig = plt.figure(figsize=(8, 12), dpi=300, frameon= False)
    
    im = Image.open(f'{path}/logos/sgc_logo.png')
    im.thumbnail((700,122), Image.ANTIALIAS)
    width, height= im.size[0],im.size[1]
    im = np.array(im).astype(np.float) / 255
    fig.figimage(im, fig.bbox.xmax - width -40, fig.bbox.ymax - height-20)
    
    # im2 = Image.open(f'{path}/logos/logo_MIN.png')
    # im2.thumbnail((1059,481), Image.ANTIALIAS)
    # width2, height2= im2.size[0],im2.size[1]
    # im2 = np.array(im2).astype(np.float) / 255
    # fig.figimage(im2, fig.bbox.xmax - width2 -40, height2)


    cmap = mpl.colors.ListedColormap(['red','orange','yellow','deepskyblue', 'limegreen'])
    bounds = [0,20,40,60,80,100]
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    
    if network=='RSNC' or network=='RNAC' or network=='SUB':
        if network == 'RSNC':   title_to_map=f'PORCENTAJE FUNCIONAMIENTO RSNC \n {date_to_map}'
        if network == 'RNAC':   title_to_map=f'PORCENTAJE FUNCIONAMIENTO RNAC \n {date_to_map}'
        if network == 'SUB':   title_to_map=f'PORCENTAJE FUNCIONAMIENTO SUB-REDES \n {date_to_map}'
        llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat= -82.1, -4.3, -66.8, 14.6
        parallels, meridians= np.arange(-4.,16.,2.) , np.arange(-82.,-66.,2.)
    if network=='INTER':
        title_to_map=f'PORCENTAJE FUNCIONAMIENTO INTERNACIONAL \n {date_to_map}'
        llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat= -93, -18, -58, 23
        parallels, meridians= np.arange(-18.,26.,4.) , np.arange(-92.,-58.,4.)
    if network=='DRL':
        title_to_map=f'PORCENTAJE FUNCIONAMIENTO DRUMMOND \n {date_to_map}'
        llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat= -73.8, 9.2, -73.2, 9.9
        parallels, meridians= np.arange(9.2,9.9,0.2) , np.arange(-73.8,-73.2,0.2)
    
    plt.title(title_to_map, fontproperties=font_prop2) 
    m = Basemap(resolution='i',projection='cyl',llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat,urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat)  
    m.arcgisimage(service='World_Shaded_Relief',xpixels = 1500, dpi=300, verbose= False)
    # m.rsnc_shadedrelief() 
    m.drawstates(linewidth=0.3, linestyle='solid', color='grey')
    m.drawcountries(color='#303338',linewidth=1.5)
    m.drawparallels(parallels,labels=[False,True,True,False],linewidth=0.15,labelstyle="+/-")
    m.drawmeridians(meridians,labels=[True,False,False,True],linewidth=0.15,labelstyle="+/-")
    x,y = m(latitud,longitud)

    sc = plt.scatter(x,y, c=percentage, cmap=cmap, norm=norm, s=0, edgecolors='none')
    cbar = plt.colorbar(sc, shrink = .7, orientation="horizontal",pad=0.05)
    cbar.set_label('PORCENTAJE',fontproperties=font_prop1)
        
    color_box=sc.to_rgba(percentage)
    for i in range(len(name)):
        plt.text(x[i], y[i], name[i],size=5.5,ha='center', weight="bold", bbox=dict(facecolor=color_box[i], edgecolor='black',pad=1))
        #plt.text(x[i], y[i],name[i], fontproperties=font_prop1)

    # plt.savefig(f'/home/ecastillo/git/SGC/SGC_noche/map_noche.png')
    plt.savefig(f'{path}/maps/map_{network}_{date}.pdf')
    time.sleep(3) #para darle tiempo de guardar

    return f"{path}/maps/map_{network}_{date}.pdf"
    #~ os.system(f"evince -f {path}/maps/map_{network}_{date}.pdf")    

def fun_json(path, date, networks):

    ip_fdsn = "http://10.100.100.232"
    port_fdsn = "8091"
    filename = f'datasta{date}.json'
    filepath = os.path.join(path,'jsons',filename)
    starttime = UTCDateTime(int(str(date[0:4])),\
                            int(str(date[4:6])),\
                            int(str(date[6:8])),0,0,0)
    endtime = starttime + datetime.timedelta(days=1)

    in_dict = {}
    for network in networks:
        in_path = os.path.join(path, 'on_stations', f'est_{network}.in')
        in_dict[network] = in_path

    sgc_perf = SGC_Performance(ip_fdsn, port_fdsn, starttime,endtime)
    sgc_perf.create_json(filepath,in_dict)

def correo_noche(path, date, mode='prueba'):         #enviar correos mode ='prueba' o 'noche'
    
    data_sender=open(f'{path}/correo/remitente_noche.txt','r' ).readlines() 
    email_sender, passw_sender = data_sender[0], data_sender[1] 
    
    if mode == 'prueba':
        with open(f"{path}/correo/destinatario_noche_prueba.json", "r") as json_file:  data = json.load(json_file)
    elif mode == 'noche':
        with open(f"{path}/correo/destinatario_noche.json", "r") as json_file:  data = json.load(json_file)
    else:
        raise Exception("el destinatario json no corresponde")

    RSNC_addressee= data[0]['CORREOS']
    RNAC_addressee= data[1]['CORREOS']
    DRL_addressee= data[2]['CORREOS']
   
    dir_histogram_folder= f'{path}/histogramas'
    dir_map_folder= f'{path}/maps'    
    dir_txt_folder= f'{path}/txt'
    dir_excel_folder= f'{path}/excel'
    net = ['RSNC','RNAC','DRL']
    
    for network in net:
        list_files_to_email= []
        print (f'\nPreparando correo...  {network}')
        if network == 'RSNC':  
            
            asunto=f'Formatos Noche {date}' 
            mensaje=open(f'{path}/correo/mensaje_noche.html',encoding='utf-8').read()%('RSNC, Sub-redes e Internaciones ')
            addressee=RSNC_addressee
            
            fundiario= 'FUNDIARIO_GENE.xls'
            informenoche= 'INFORMENOCHE2.xls'
            dir_fundiario= os.path.join(dir_excel_folder,  fundiario) 
            dir_informenoche= os.path.join(dir_excel_folder,  informenoche) 

            list_files_to_email.append((fundiario, dir_fundiario))
            list_files_to_email.append((informenoche, dir_informenoche))
            
            networks= ['RSNC','SUB','INTER']
            for _network in networks:
                histogram= f'hist_{_network}_{date}.pdf'
                Map= f'map_{_network}_{date}.pdf'
                
                dir_histogram= os.path.join(dir_histogram_folder,  histogram) 
                dir_map= os.path.join(dir_map_folder,  Map) 
                
                list_files_to_email.append((histogram,dir_histogram))
                list_files_to_email.append((Map,dir_map))
     
        if network=='RNAC': 
            
            asunto= f'Formatos Noche {date}'
            mensaje=open(   f'{path}/correo/mensaje_noche.html',encoding='utf-8').read()%('RNAC')
            addressee=RNAC_addressee
            
            histogram= f'hist_{network}_{date}.pdf'
            Map= f'map_{network}_{date}.pdf'
            txt= f'func{network}{date}.txt'
            
            dir_histogram= os.path.join(dir_histogram_folder,  histogram) 
            dir_map= os.path.join(dir_map_folder,  Map) 
            dir_txt= os.path.join(dir_txt_folder,  txt) 
            
            list_files_to_email.append((histogram, dir_histogram))
            list_files_to_email.append((Map,dir_map))
            list_files_to_email.append((txt,dir_txt))
            
        if network=='DRL':  
            asunto=f'Formatos Noche Funcionamiento Estaciones Drummond {date}'
            mensaje=open(   f'{path}/correo/mensaje_noche.html',encoding='utf-8').read()%('DRUMMOND')
            addressee=DRL_addressee

            histogram= f'hist_{network}_{date}.pdf'
            Map= f'map_{network}_{date}.pdf'
            txt= f'func{network}{date}.txt'
            
            dir_histogram= os.path.join(dir_histogram_folder,  histogram) 
            dir_map= os.path.join(dir_map_folder,  Map) 
            dir_txt= os.path.join(dir_txt_folder,  txt) 
            
            list_files_to_email.append((histogram, dir_histogram))
            list_files_to_email.append((Map,dir_map))
            list_files_to_email.append((txt,dir_txt))

        msg = MIMEMultipart()
        msg['From'] = 'SGC <rsncol@sgc.gov.co>'
        if isinstance(addressee,str):   msg['To'] =  addressee
        if isinstance(addressee,list):   msg['To'] =  ", ".join(addressee)  
        msg['Subject'] = asunto
        msg.attach(MIMEText(mensaje, 'html'))
        
        for _file in list_files_to_email:
            filename, filedir= _file[0], _file[1]
            attachment = open( filedir,'rb')
            part= MIMEBase('aplication','octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= "+filename)   
            msg.attach(part)
            
        # server = smtplib.SMTP('smtp.gmail.com:25') 
        server = smtplib.SMTP('smtp.gmail.com:587') 
        server.starttls()
        server.login(email_sender,passw_sender)
        server.sendmail(email_sender, addressee, msg.as_string())
        server.quit()
        print (f"Correo enviado:  {network}")

def pdf_merger(path, date, input_paths):
    
    output_path = f"{path}/pdf_noche/noche_{date}.pdf"
    pdf_writer = PdfFileWriter()
    for path in input_paths:
        try:
            pdf_reader = PdfFileReader(path)
            for page in range(pdf_reader.getNumPages()):
                pdf_writer.addPage(pdf_reader.getPage(page))
        except:
            print(f"No se encontro el archivo {path} ")      
    with open(output_path, 'wb') as fh:
        pdf_writer.write(fh)

def correo_problema(path, date, mode='prueba'):
    
    data_sender=open(f'{path}/correo/remitente_noche.txt','r').readlines() 
    email_sender, passw_sender = data_sender[0], data_sender[1]

    if mode == 'prueba':
        with open(f"{path}/correo/destinatario_problema_prueba.json", "r") as json_file:  data = json.load(json_file)
    elif mode == 'noche':
        with open(f"{path}/correo/destinatario_problema.json", "r") as json_file:  data = json.load(json_file) 
    else:
        raise Exception("el destinatario json no corresponde")


    
    asunto=f'Problema en Formatos Noche {date}' 

    os.system(f'nano {path}/problemas/problema_{date}.txt')
    problema= open(f"{path}/problemas/problema_{date}.txt","r").read()
    mensaje=open(   f'{path}/correo/mensaje_problema.html', encoding='utf-8').read()%(f'{problema}')
    addressee=data[0]['CORREOS']

    list_files_to_email= [(f"noche_{date}.pdf",f"{path}/pdf_noche/noche_{date}.pdf")]
    #~ 
    msg = MIMEMultipart()
    msg['From'] = 'SGC <rsncol@sgc.gov.co>'
    if isinstance(addressee,str):   msg['To'] =  addressee
    if isinstance(addressee,list):   msg['To'] =  ", ".join(addressee)  
    msg['Subject'] = asunto
    msg.attach(MIMEText(mensaje, 'html'))
    #~ 

    """
    # Es mejor no agregar el pdf al correo de problemas
    print("Espere un momento...")
    for _file in list_files_to_email:
        filename, filedir= _file[0], _file[1]
        attachment = open( filedir,'rb')
        part= MIMEBase('aplication','octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= "+filename)   
        msg.attach(part)
        #~ 
    """
    server = smtplib.SMTP('smtp.gmail.com:25') 
    server.starttls()
    server.login(email_sender,passw_sender)
    server.sendmail(email_sender, addressee, msg.as_string())
    server.quit()
    print (f"Problema enviado a {addressee}")

if __name__ == "__main__":
    repository = os.path.dirname(os.path.abspath(__file__))
    PATH = os.path.join(repository,'bin')

    PATH = '/home/ecastillo'
    func_map(PATH,'RSNC','20200820')
    # correo_problema(PATH,'20200108')
