import math
import os
import re
import subprocess
import json
import sys
import threading

def write_to_file(output_string, file_path):
    with open(file_path, 'w') as output_file:
        output_file.write(output_string)

def load_json(path):
    with open(path) as file:
        obj = json.load(file)
    return obj

def get_network_bandwidth(input_string):
    # Define a regular expression pattern
    pattern = r'Network:\s*([\d,]+)'

    # Search for the pattern in the input string
    match = re.search(pattern, input_string)

    return match.group(1).split(',')[0]

def figure(algo2='../ComycoLin/ComycoLin.py', fig_name = 'fig', label='ComycoLin'):
    algo1='bola'

    completed = subprocess.run(['python3', './../../src/sabre.py', '-v',
                                '-m', 'bbb.json', 
                                '-a', algo1, '-ab'],
                               stdout = subprocess.PIPE)
    algo1Results = completed.stdout.decode('ascii')

    completed = subprocess.run(['python3', './../../src/sabre.py', '-v',
                                '-m', 'bbb.json',
                                '-a', algo2],
                               stdout = subprocess.PIPE)
    algo2Results = completed.stdout.decode('ascii')

    write_to_file(algo1Results, 'tmp/fig-{}.log'.format(algo1))
    write_to_file(algo2Results, 'tmp/fig-{}.log'.format(algo2.split('/')[1]))

    fig1 = []

    for out in [algo1Results, algo2Results]:
        fig = []
        for line in out.split('\n'):
            if not '[' in line or 'Network' in line:
                continue
            l = line.split()
            
            quality = int(l[2].split('=')[1]) 
            
            quality = bbb['bitrates_kbps'][quality] / 1000
            timestamp = line.split("]")[0].split("[")[1]
            start_time = int(timestamp.split("-")[0])
            
            fig += [(start_time / 1000, quality)]

            timestamp_end = int(timestamp.split("-")[1]) - start_time
            buffer_level = int(line.split("->")[0].split("bl=")[1])

            if timestamp_end <= buffer_level:
                end_time = start_time + timestamp_end
                fig += [(end_time / 1000, quality)]
            else:
                end_time = start_time + buffer_level
                fig += [(end_time / 1000, quality)]
                fig += [((end_time / 1000)+0.1, 0)]

            # if index == 9:
            #     break

        fig1 += [fig]


    fig = []
    for line in algo1Results.split('\n'):
        if 'Network' in line:
            time = int(line.split("]")[0].split("[")[1])
            bandwidth = get_network_bandwidth(line)
            fig += [(float(time / 1000), float(bandwidth))]
    fig1 += [fig]

    # Write data to file
    for i in [0, 1, 2]:
        name = 'fig1%s.dat' % ['a', 'b', 'c'][i]
        with open('tmp/%s' % name, 'w') as f:
            for l in fig1[i]:
                f.write('%f %f\n' % (l[0], l[1]))

    plotting = '''set term pdf size 9,3 font ",16"
set bmargin 3.5

set style data lines
set yrange[0:6.5]

set xlabel 'time (s)'
set ylabel 'bitrate (mbps)'

set xtics 100

#set key bottom right
set key out top center
set output "figures/{0}.pdf"

plot "tmp/fig1a.dat" title "BOLA" lc 7 dt 4 lw 2, "tmp/fig1b.dat" title "{1}" lc 6 lw 1 with steps, 

set output
'''.format(fig_name, label)

    subprocess.run('gnuplot', input = plotting.encode('ascii'))

def figure2(algo = 'bola', fig_name = 'fig'):
    completed = subprocess.run(['python3', './../../src/sabre.py', '-v',
                                '-m', 'bbb.json', 
                                '-a', algo, '-ab'],
                               stdout = subprocess.PIPE)
    result_logs = completed.stdout.decode('ascii')

    write_to_file(result_logs, 'tmp/{}.log'.format(fig_name))

    fig1 = []

    # bitrate plot
    for out in [result_logs]:
        fig = []
        for line in out.split('\n'):
            if not '[' in line or 'Network' in line:
                continue
            l = line.split()
            
            quality = int(l[2].split('=')[1]) 
            
            quality = bbb['bitrates_kbps'][quality]
            timestamp = line.split("]")[0].split("[")[1]
            start_time = int(timestamp.split("-")[0])
            
            fig += [(start_time / 1000, quality)]

            timestamp_end = int(timestamp.split("-")[1]) - start_time
            buffer_level = int(line.split("->")[0].split("bl=")[1])

            if timestamp_end <= buffer_level:
                end_time = start_time + timestamp_end
                fig += [(end_time / 1000, quality)]
            else:
                end_time = start_time + buffer_level
                fig += [(end_time / 1000, quality)]
                fig += [((end_time / 1000)+0.1, 0)]

            # if index == 9:
            #     break

        fig1 += [fig]

    # buffer level plot
    fig = []
    for line in result_logs.split('\n'):
        if not '[' in line or 'Network' in line:
            continue
        
        l = line.split()
        time = int(line.split("]")[0].split("[")[1].split("-")[0])
        buffer_level = int(line.split("->")[1])
        fig += [(float(time / 1000), float(buffer_level / 1000))]

    fig1 += [fig]

    # Write data to file
    for i in [0, 1]:
        name = '{}%s.dat'.format(fig_name) % ['a', 'b', 'c'][i]
        with open('tmp/%s' % name, 'w') as f:
            for l in fig1[i]:
                f.write('%f %f\n' % (l[0], l[1]))

    plotting = '''set term pdf size 16.0, 2.75 font ",16"
set bmargin 3.5

set style data lines
set yrange[0:6500]

set xlabel 'time (s)'
set ylabel 'bitrate (kbps)'

set xtics 200

#set key bottom right
set key out top center

set output "figures/{1}.pdf"

plot "tmp/{1}a.dat" title "{0}" lc 7 dt 4 lw 2

set ylabel 'Buffer Level (s)'
set yrange [0:30]
plot "tmp/{1}b.dat" title "BufferLevel" lc 8 lw 2 

set output
'''.format(algo, fig_name)

    subprocess.run('gnuplot', input = plotting.encode('ascii'))

if __name__ == '__main__':

    bbb = load_json('bbb.json')
    bbb4k = load_json('bbb4k.json')

    os.makedirs('tmp', exist_ok = True)
    os.makedirs('figures', exist_ok = True)
    os.makedirs('stats', exist_ok = True)

    figure(fig_name='figComycoLin', label='ComycoLin')
    figure('../Pensieve/Pensieve.py', fig_name='figPensieve', label='Pensieve')
    figure2(algo='bola', fig_name='figA')
    figure2(algo='../ComycoLin/ComycoLin.py', fig_name='figB')
    figure2(algo='../Pensieve/Pensieve.py', fig_name='figC')
   
