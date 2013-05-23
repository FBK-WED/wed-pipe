""" questo file non e' inteso per essere usato come script, e' stato
scritto per convertire le coordinate di un file csv e non mi pareva
il caso di buttare il codice, tutto qui
"""


from pyproj import transform, Proj

p1 = Proj(init='epsg:23032')
p2 = Proj(init='epsg:4326')
fin_name = '/Users/stefanop/Dropbox/Venturi/archiveItems/ISTAT-LAU3.csv'
fout_name = '/Users/stefanop/Desktop/ISTAT-LAU3b.csv'

header = {}
with open(fin_name) as fin, open(fout_name, 'w') as fout:
    for line in fin:
        cells = line.strip().split(';')
        if not header:
            header = {y:x for x, y in enumerate(cells)}
            fout.write('{0};lat;lon\n'.format(line.strip()))
            continue
        lon, lat = transform(p1, p2, cells[header['xcoord']], cells[header['ycoord']])
        fout.write('{0};{1};{2}\n'.format(line.strip(), lat, lon))
