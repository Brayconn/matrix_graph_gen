import copy, itertools, queue

def weighted_sum(l, b):
    return sum((b**i)*n for i,n in enumerate(l))

class matrix:
    def __init__(self, rows, base=3):
        self.rows = rows
        self.base = base
    
    def AddRows(self,r1:int,r2:int,scalar:int):
        for i in range(len(self.rows[r1])):
            self.rows[r1][i] = (self.rows[r1][i] + ((scalar*self.rows[r2][i])%self.base) ) % self.base
    
    def copy(self):
        return matrix(copy.deepcopy(self.rows),base=self.base)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
    
    def __ne__(self, other):
        return not (self.__hash__() == other.__hash__())
    
    def __hash__(self):
        val = weighted_sum([i for s in self.rows for i in s],3)
        #print("Hashed " + str(self.rows) + " to " + str(val))
        return val
    
    def __str__(self):
        s = ""
        for r in self.rows:
            s += str(r) +"\\n"
        return s

def get_hashes(l):
    return ', '.join([str(x.__hash__()) for x in l])

BASE = 3
#9677, 5465, 9781, 8377, 5413, 8221
STARTS = []
for p in itertools.permutations([[2, 0, 1],[1, 2, 0],[1, 1, 1]], BASE):
    STARTS.append(matrix(p,BASE))

# 6643, 2431, 6591, 975, 2223, 819
DESTINATIONS = []
for p in itertools.permutations([[1,0,0],[0,1,0],[0,0,1]]):
    DESTINATIONS.append(matrix(p,BASE))

START = DESTINATIONS[0]

MAX = BASE**(len(START.rows)*len(START.rows[0]))

POSSIBILITIES = set()
def found_destination():
    return any(d in POSSIBILITIES for d in DESTINATIONS)

EDGES = {}
q = queue.LifoQueue()
q.put(START)

INCLUDE_SELF_TRANSITIONS = True

ROWS = len(START.rows)
COLUMNS = len(START.rows[0])
STATES = BASE**(ROWS*COLUMNS)
OPS=STATES*(ROWS*ROWS*(BASE-1))
print("Predicted total edges for this graph: " + str(OPS))

while not q.empty():
    #print("Items left: " + str(q.qsize()))
    if q.qsize() > MAX*MAX:
        print("GOING TO INFINITY!!!")
        exit(2)
    #if found_destination():
        #print("Found a goal!!!")
        #break

    p = q.get_nowait()
    POSSIBILITIES.add(p)
    h = p.__hash__()

    for r1 in range(len(START.rows)):
        for r2 in range(len(START.rows)):
            for s in range(1,BASE):
                _p = p.copy()
                _p.AddRows(r1,r2,s)
                if _p not in POSSIBILITIES:
                    q.put(_p)
                dh = _p.__hash__()
                if INCLUDE_SELF_TRANSITIONS or not h == dh:
                    if not (h,dh) in EDGES:
                        EDGES[(h,dh)] =set([(r1,s,r2)])
                    else:
                        EDGES[(h,dh)].add(((r1,s,r2)))

print("Sources are: " + get_hashes(STARTS))
print("Destinations are: " + get_hashes(DESTINATIONS))
print("A path exists!" if found_destination() else "No path exists...")
print(str(len(POSSIBILITIES)) + " Nodes, " + str(len(EDGES)) + " Edges")

combinations_found = sum(len(x) for x in EDGES.values())
self_transitions = sum(len(v) for k,v in EDGES.items() if k[0] == k[1])

print(str(combinations_found) + " Row Operations, " + str(self_transitions) + " Self Transitions, " + str(len(EDGES) - self_transitions) + " Unique Transitions")


def make_edge_desc(e):
    d = ""
    for w in e:
        d += "R" + str(w[0]+1) + " += " + str(w[1]) + "*R" + str(w[2]+1) + "\\n"
    return d

def make_plantuml(path):
    OUTPUT = "@startuml\n[*] --> " + str(START.__hash__()) + "\n"
    for p in POSSIBILITIES:
        OUTPUT += str(p.__hash__()) + ": " + str(p) + "\n"

    for k,v in EDGES.items():
        OUTPUT += str(k[0]) + " --> " + str(k[1]) + ": "
        OUTPUT += make_edge_desc(v)
        OUTPUT += "\n"

    OUTPUT += "@enduml"
    with open(path, "w") as of:
        of.write(OUTPUT)

#make_plantuml("matrix.wsd")

def make_graphviz(path):
    dot = graphviz.Digraph(comment="Possibilities from " + str(START.__hash__()))

    for p in POSSIBILITIES:
        dot.node(str(p.__hash__()), str(p))
    for k,v in EDGES.items():
        dot.edge(str(k[0]),str(k[1]), make_edge_desc(v))

    dot.save(path)

#make_graphviz("source_self.dot")


