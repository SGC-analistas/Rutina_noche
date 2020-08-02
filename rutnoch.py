"""
-*- coding: utf-8 -*-
Rutina de la noche
Angel Daniel A., Emmanuel C., 
2020 I
"""
import os
import time
import itertools
import warnings
import fun_noche as no
import concurrent.futures
from funest import SGC_Performance
from colorama import init, Fore, Back
init(autoreset=True)

def map_hist(net,fecha):

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mapa= no.func_map(net, fecha)									#crear mapas
        histo= no.histograma(net,fecha)								#crear histogramas
        return histo, mapa

def run (path, fecha):
    estaciones = ["RSNC","RNAC","SUB","DRL","INTER"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        print(f'...loading json: {fecha}')
        no.fun_json(fecha) 
        print(f'...loading txts: {fecha}')
        no.edit_fun(fecha) 		#para editar los txt
        for net in estaciones:
            os.system(f"nano {path}/txt/func{net}{fecha}.txt")

        pdf_file=[]
        with concurrent.futures.ProcessPoolExecutor() as executor:
            print(f'...loading maps: {fecha}')
            results= executor.map( map_hist, estaciones , itertools.repeat(fecha))
            for result in results:  
                pdf_file.append(result[0])
                pdf_file.append(result[1])

        no.pdf_merger(f"{path}/pdf_noche/noche_{fecha}.pdf", pdf_file)
        os.system(f"evince {path}/pdf_noche/noche_{fecha}.pdf") 
        print(f'...loading excel: {fecha}')
        no.info_excel(fecha)										#editar excel

        condicion= True
        while condicion == True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("¿Desea enviar correos?")
            print(Fore.GREEN + "\t 1","[si]","    ",Fore.RED + "0","[no]"  )
            p = input()
            if p == "1":
                #~ no.correo_noche(fecha)
                condicion = False
            if p == "0":
                print(Fore.RED +"¿Desea informar el problema?.")
                print(Fore.GREEN + "\t 1","[si]","    ",Fore.RED + "0","[no]"  )
                p = input()
                if p == "1":
                    no.correo_problema(fecha)
                    condicion = False
                if p == "0":
                    condicion = False

if __name__ == "__main__":
    path = "/mnt/almacenamiento/Emmanuel_Castillo/NOCHE"
    fecha = input("\n\tfecha YYYYMMDD:  ")
    run (path, fecha)

