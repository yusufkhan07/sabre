import math
import os
import subprocess
import json
import sys
import threading

def load_json(path):
    with open(path) as file:
        obj = json.load(file)
    return obj

def figure():
    completed = subprocess.run(['python3', './../../src/sabre.py', '-v',
                                '-m', 'bbb.json', 
                                '-a', 'bola', '-ab'],
                               stdout = subprocess.PIPE)
    bola = completed.stdout.decode('ascii')

    completed = subprocess.run(['python3', './../../src/sabre.py', '-v',
                                '-m', 'bbb.json',
                                '-a', '../ComycoLin/ComycoLin.py'],
                               stdout = subprocess.PIPE)
    bolapl = completed.stdout.decode('ascii')

    fig1 = []
    for out in [bola, bolapl]:
        fig = []
        for line in out.split('\n'):
            if not '[' in line or 'Network' in line:
                continue
            l = line.split()
            
            index = int(l[1].split(':')[0])
            quality = int(l[2].split('=')[1])
            #print('%d %d' % (index, quality))
            fig += [(index * 3, bbb['bitrates_kbps'][quality])]
            fig += [((index + 1) * 3, bbb['bitrates_kbps'][quality])]
            if index == 9:
                break

        fig1 += [fig]

    for i in [0, 1]:
        name = 'fig1%s.dat' % ['a', 'b'][i]
        with open('tmp/%s' % name, 'w') as f:
            for l in fig1[i]:
                f.write('%f %f\n' % (l[0], l[1]))

    plotting = '''set term pdf size 1.9, 1.75 font ",16"
set bmargin 3.5

set style data lines
set yrange[0:6500]

set xlabel 'play time (s)'
set ylabel 'bitrate (kbps)'

set xtics 10

#set key bottom right
set key out top center

set output "figures/fig.pdf"

plot "tmp/fig1a.dat" title "BOLA" lc 7 dt 4 lw 2, "tmp/fig1b.dat" title "BOLA-PL" lc 6 lw 2

set output
'''
    subprocess.run('gnuplot', input = plotting.encode('ascii'))

if __name__ == '__main__':

    bbb = load_json('bbb.json')
    bbb4k = load_json('bbb4k.json')

    os.makedirs('tmp', exist_ok = True)
    os.makedirs('figures', exist_ok = True)
    os.makedirs('stats', exist_ok = True)

    figure()
   
