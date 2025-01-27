#!/usr/bin/env python


#### This script is to correct the xml files exported from Windows StimPlan simulation due to a bug in it.

#### This is a bug in the export xml-file from Windows StimPlan and it occurs in some cases. 
#### We have communicated this with StimPlan vendor NSI earlier, and it is probably fixed in newer versions of StimPlan. 

#### The error in the xml-file is an extra “xs” fracture length data point in the negative direction. 
#### These negative “xs” are used for “Asymmetric” fractures, but not for “Symmetric” fractures which are normally simulated. 
#### This results in that ResInsight interprets this to have one fracture wing with 0’s and the other wing with normal properties.
#### <xs><![CDATA[-3.99995 0 3.99995 7.9999 ….
#### <![CDATA[0.000000 6.521342 6.308681 5.975412
#### the first data point for “xs” and “CDATA”’s need to be deleted. And “grid xCound” needs to be reduced by 1.



import shutil

def xml_corr(file):
    with open(file) as f:
        lines = f.readlines()
    
    # check whether there is only one negative number in the line #2
    if len(lines[2].split())==1 and '-' in lines[2]:# float((lines[2].split("[CDATA[")[-1]))<0:
        
        # make a copy of the input file and preserve its timestamp
        shutil.copy2(file, file.split('.')[0]+'_orig.'+file.split('.')[-1])
    
        # update line #2
        print(f'Original line #2: {lines[2]}')
        tmp = lines[2].split("[CDATA[")[-1]
        lines[2] = lines[2].replace(tmp, '\n')
        print(f'Updated line #2: {lines[2]}')
    
        # update line # 1
        print(f'\nOriginal line #1: {lines[1]}')
        nx_orig = lines[1].split('"')[1]
        nx_new = str(int(nx_orig)-1)
        lines[1] = lines[1].replace(nx_orig, nx_new)
        print(f'Updated line #1: {lines[1]}')
    
        for idx, line in enumerate(lines):
            if '<properties>' in line:
                index_properties = idx
        #print(index_properties)
    
        with open(file, 'w') as f:
            for idx, line in enumerate(lines):
                if idx <= index_properties+3:
                    f.write(line)
                elif '<![CDATA[' in line:
                    line = line.replace(line.split()[0], '<![CDATA[')
                    f.write(line)
                else:
                    f.write(line)
    else:
        print('\nNo correction is necessary')
    return


files = ['big_job_no.XML']
for file in files:
    print(f'\n##################### Processing file: {file} #####################')
    xml_corr(file)


        
