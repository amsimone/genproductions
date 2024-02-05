#!/usr/bin/env python

'''
Script for ReneSANCe generator production
'''

import sys
import os
import re
import shutil
from glob import glob
from optparse import OptionParser

def main():
    parser = OptionParser()
    parser.add_option('-c', '--commands', dest="commands", default= 'checkout,compile,run,pack', help='commands/stages to run')
    parser.add_option('-f', '--folderName', dest="dir", default='inputdir', help='local folder name [input]')
    parser.add_option('-i', '--input', dest="cfg", default= 'inputcfg', help='input cfg folder [input]')
    parser.add_option('-v', '--version', dest="version", default= '1.3.8', help='version number [version]')

    (args, opts) = parser.parse_args(sys.argv)
    print(args)

    if 'checkout' in args.commands:
        checkout(args)

    if 'compile' in args.commands:
        compile(args)

    if 'run' in args.commands:
        run(args)

    if 'pack' in args.commands:
        pack(args)



def checkout(args):
    print('Checking out Renesance')
    if not os.path.exists(args.dir):
        os.mkdir(args.dir)

        import requests
        import tarfile

	url = 'https://renesance.hepforge.org/downloads?f=ReneSANCe-'+args.version+'.tar.gz'
	try:
            response = requests.get(url, allow_redirects=True, verify=False, stream=True)
	except requests.exceptions.RequestException:
            print("Failed to download file: {}".format(url))
            exit(1)
	tarball = tarfile.open(fileobj=response.raw, mode="r|gz")
        tarball.extractall(path=args.dir)



def compile(args):
    print('Compiling Renesance')
    cwd = os.getcwd()+'/'
    os.chdir(args.dir+'/ReneSANCe-'+args.version+'/build/')
    os.system('cmake ..')
    os.system('make -j')
    os.system('make install')
    os.chdir(cwd)



def run(args):
    print('Run Renesance')
    cwd = os.getcwd()+'/'
    print('c=',cwd)
    print('i=',args.cfg)
    print('d=',cwd+args.dir+'/input')
    #shutil.copy(cwd+args.cfg, cwd+args.dir+'/input')
	
    shutil.copytree(cwd+args.dir+'/ReneSANCe-'+args.version+'/share',   packdir+'/share')
    shutil.copytree(cwd+args.cfg, cwd+args.dir+'/ReneSANCe-'+args.version+'/input')
    os.chdir(args.dir+'/ReneSANCe-'+args.version)
    os.system('./bin/renesance_pp -f input')
    os.chdir(cwd)



def pack(args):
    print('Packing gridpack')
    cwd = os.getcwd()+'/'
    packdir = cwd+args.dir+'/pack/'
    if os.path.exists(packdir):
	    shutil.rmtree(packdir)
    os.mkdir(packdir)

    ### copy all files to gridpack folder                                                                                           
    shutil.copytree(cwd+args.dir+'/ReneSANCe-'+args.version+'/input',   packdir+'/input')
    for grid in glob(cwd+args.dir+'/ReneSANCe-'+args.version+'/Foam*.root'):
	shutil.copy(grid, packdir+grid.split('/')[-1])
    shutil.copy(cwd+args.dir+'/ReneSANCe-'+args.version+'/bin/renesance_pp',   packdir+'/renesance_pp')

    ### set to false grid creation in proc card                                                                                     
    with open(packdir+'/input/proc.conf', 'r') as file:
	proc_card = file.read()

    proc_card = re.sub(r"(explore\w*)\s*:\s*true",
		       r"\1: false",
		       proc_card,
		       flags=re.MULTILINE)

    # enable generation of LHE                                                                                                      
    proc_card = re.sub(r"(printLHE)\s*:\s*false",
		       r"\1: true",
		       proc_card)
    with open(packdir+'/input/proc.conf', 'w') as file:
	file.write(proc_card)


    scram_arch = os.getenv('SCRAM_ARCH')
    cmssw_version = os.getenv('CMSSW_VERSION')
    shutil.copy(cwd+'/runcmsgrid_renesance.sh', packdir+'/runcmsgrid.sh')
    os.chdir(packdir)
    os.system('sed -i s/SCRAM_ARCH_VERSION_REPLACE/%s/g runcmsgrid.sh' % scram_arch)
    os.system('sed -i s/CMSSW_VERSION_REPLACE/%s/g runcmsgrid.sh' % cmssw_version)
    os.chdir(cwd)

    import tarfile
    tarname = scram_arch+'_'+cmssw_version+'_'+args.dir+'.tar.gz'
    print(tarname)
    with tarfile.open(tarname, "w:gz") as tar:
        tar.add(packdir, arcname=os.path.basename(packdir))




if __name__ == "__main__":
    main()



