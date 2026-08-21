# -*- coding: utf-8 -*-
"""连通性审计：每网络的焊盘/过孔/走线必须构成单一连通分量（NC 除外）。"""
import math, importlib.util, sys
spec = importlib.util.spec_from_file_location("gen_board", "/Users/bruce/Desktop/IPQ/工程文件/pcb/gen_board.py")
gb = importlib.util.module_from_spec(spec)
sys.modules['gen_board'] = gb
import os
os.chdir("/Users/bruce/Desktop/IPQ/工程文件/pcb")
# 只执行定义，不执行 __main__
spec.loader.exec_module(gb)

def seg_pt_dist(px,py, ax,ay,bx,by):
    abx, aby = bx-ax, by-ay
    L2 = abx*abx+aby*aby
    if L2 == 0: return math.hypot(px-ax,py-ay)
    t = max(0, min(1, ((px-ax)*abx+(py-ay)*aby)/L2))
    return math.hypot(px-(ax+abx*t), py-(ay+aby*t))

# 收集每网络的“节点”：焊盘、过孔、走线段
from collections import defaultdict
net_nodes = defaultdict(list)   # net -> list of ('pad'/'via', x,y,r) or ('seg',(p1,p2),w)
for p in gb.pads:
    if p['net']=='NC': continue
    net_nodes[p['net']].append(('pt', p['x'],p['y'], p['pad']/2))
for v in gb.vias:
    net_nodes[v['net']].append(('pt', v['x'],v['y'], gb.VIA_PAD/2))
for t in gb.tracks:
    for i in range(len(t['pts'])-1):
        net_nodes[t['net']].append(('seg', (t['pts'][i],t['pts'][i+1]), t['w']/2))

# 连通性：点-点 相交 / 点-段 相交 / 段-段 相交
def touch(a, b):
    if a[0]=='pt' and b[0]=='pt':
        return math.hypot(a[1]-b[1], a[2]-b[2]) <= a[3]+b[3]+0.05
    if a[0]=='pt' and b[0]=='seg':
        (x,y),r = (a[1],a[2]),a[3]; (p1,p2),w = b[1],b[2]
        return seg_pt_dist(x,y,p1[0],p1[1],p2[0],p2[1]) <= r+w+0.05
    if a[0]=='seg' and b[0]=='pt':
        return touch(b,a)
    (p1,p2),w1 = a[1],a[2]; (q1,q2),w2 = b[1],b[2]
    def segseg(a1,a2,b1,b2):
        ds = [seg_pt_dist(b1[0],b1[1],a1[0],a1[1],a2[0],a2[1]),
              seg_pt_dist(b2[0],b2[1],a1[0],a1[1],a2[0],a2[1]),
              seg_pt_dist(a1[0],a1[1],b1[0],b1[1],b2[0],b2[1]),
              seg_pt_dist(a2[0],a2[1],b1[0],b1[1],b2[0],b2[1])]
        return min(ds) <= w1+w2+0.05
    return segseg(p1,p2,q1,q2)

bad = 0
POUR_NETS = {'GND'}   # 底层整板铺铜网络：所有焊盘经热焊盘辐条接入铺铜，天然连通
for net, nodes in sorted(net_nodes.items()):
    if net in POUR_NETS: continue
    n = len(nodes)
    parent = list(range(n))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def uni(x,y): parent[find(x)] = find(y)
    for i in range(n):
        for j in range(i+1,n):
            if touch(nodes[i],nodes[j]): uni(i,j)
    comps = len({find(i) for i in range(n)})
    if comps > 1:
        bad += 1
        print('[FAIL] 网络 %-10s 分成 %d 个连通分量（%d 个节点）' % (net, comps, n))
        # 输出各组以定位
        groups = defaultdict(list)
        for i in range(n):
            nd = nodes[i]
            tag = ('PT %.1f,%.1f' % (nd[1],nd[2])) if nd[0]=='pt' else ('SEG %s-%s' % (nd[1][0],nd[1][1]))
            groups[find(i)].append(tag)
        for g,tags in groups.items():
            print('   组:', tags[:8], '...' if len(tags)>8 else '')
if bad == 0:
    print('[PASS] 全部 %d 个网络单一连通分量，无断线' % len(net_nodes))
