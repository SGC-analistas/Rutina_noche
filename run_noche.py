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
import utils_noche as no
import concurrent.futures
from colorama import init, Fore, Back
init(autoreset=True)

def map_hist(net,fecha,path):

    mapa= no.func_map(path,net, fecha)									#crear mapas
    histo= no.histograma(path,net,fecha)								#crear histogramas
    return histo, mapa

def run (path, fecha, mode = 'prueba'):                 #enviar correos mode ='prueba' o 'noche'
    nets = ["RSNC","RNAC","SUB","DRL","INTER"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        json_file = os.path.join(path,'jsons', f'datasta{fecha}.json')
        if os.path.isfile(json_file) == True:
            condicion= True
            while condicion == True:
                print(Fore.RED + f"\nEl json ya existe!,   Desea crear un nuevo json?")
                print(Fore.GREEN + "\t 1","[si]","    ",Fore.RED + "0","[no]"  )
                p = input()
                if p == "1":
                    print(f'...loading json: {fecha}')
                    tic = time.time()
                    no.fun_json(path,fecha,nets) 
                    toc = time.time()
                    print("{0:>15}".format(f'json delay: {toc-tic:.2f}s'))
                    break
                elif p == "0":    
                    break
        else:
            print(f'...loading json: {fecha}')
            tic = time.time()
            no.fun_json(path,fecha,nets) 
            toc = time.time()
            print("{0:>15}".format(f'json delay: {toc-tic:.2f}s'))


        print(f'...loading txts: {fecha}')
        no.edit_fun(path,fecha) 		#para editar los txt
        for net in nets:
            os.system(f"nano {path}/txt/func{net}{fecha}.txt")


        pdf_file=[]
        with concurrent.futures.ProcessPoolExecutor() as executor:
            print(f'...loading maps: {fecha}')
            results= executor.map( map_hist, nets , itertools.repeat(fecha), itertools.repeat(path))
            for result in results:  
                pdf_file.append(result[0])
                pdf_file.append(result[1])

        no.pdf_merger(path, fecha, pdf_file)
        os.system(f"evince {path}/pdf_noche/noche_{fecha}.pdf") 


        print(f'...loading excel: {fecha}')
        no.info_excel(path,fecha)										#editar excel

        condicion= True
        while condicion == True:
            # os.system('cls' if os.name == 'nt' else 'clear')
            print("Desea enviar correos?")
            print(Fore.GREEN + "\t 1","[si]","    ",Fore.RED + "0","[no]"  )
            p = input()
            if p == "1":
                no.correo_noche(path,fecha,mode=mode)
                break
            if p == "0":
                print(Fore.RED +"Desea informar el problema?.")
                print(Fore.GREEN + "\t 1","[si]","    ",Fore.RED + "0","[no]"  )
                p = input()
                if p == "1":
                    no.correo_problema(path,fecha,mode=mode)
                    break
                if p == "0":
                    break


if __name__ == "__main__":
    repository = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(repository,'noche_store')
    fecha_ok = False
    while fecha_ok != True:
        fecha = input("\n\tfecha YYYYMMDD:  ")
        if len(fecha) == 8:
            fecha_ok = True
            run(path, fecha, mode='noche') #mode : prueba o mode : noche
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("digito mal la fecha. Intente de nuevo")


