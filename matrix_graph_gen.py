#bin/python3
#Made by Brayconn
#MIT license
import argparse, copy, itertools, queue, logging, re, sys
from typing import List, Set, Dict, Tuple

def weighted_sum(l, b):
    return sum((b**i)*n for i,n in enumerate(l))

class matrix:
    def __init__(self, rows:List[List[int]], base:int=-1):
        self.rows = rows
        self.base = base
        if self.base < 2:
            self.base = max(i for r in self.rows for i in r)+1
            logging.debug("Auto determined base to be " + str(self.base))
        if self.base < 2:
            raise Exception("Invalid base: " + str(self.base))
    
    def AddRows(self, r1:int, r2:int, scalar:int):
        for i in range(len(self.rows[r1])):
            self.rows[r1][i] = (self.rows[r1][i] + (scalar*self.rows[r2][i])) % self.base
    
    def AddColumns(self, c1:int, c2:int, scalar:int):
        for i in range(len(self.rows)):
            self.rows[i][c1] = (self.rows[i][c1] + (scalar*self.rows[i][c1])) % self.base

    def copy(self):
        return matrix(copy.deepcopy(self.rows),base=self.base)
    
    def properties_eq(self, other):
        return len(self.rows) == len(other.rows) and \
               len(self.rows[0]) == len(other.rows[0]) and \
               self.base == other.base

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
    
    def __ne__(self, other):
        return not (self.__hash__() == other.__hash__())
    
    def __hash__(self):
        val = weighted_sum([i for s in self.rows for i in s],self.base)
        #logging.debug("Hashed " + str(self.rows) + " to " + str(self.hash))
        return val
    
    def __str__(self):
        s = ""
        for r in self.rows:
            s += str(r) +"\\n"
        return s

def get_hashes(l):
    return ', '.join([str(x.__hash__()) for x in l])

def make_graph(inputs:List[matrix], ends:List[matrix], stop_criteria:str, stop_behavior:str, include_self_transitions:bool):
    ROWS = len(inputs[0].rows)
    COLUMNS = len(inputs[0].rows[0])
    BASE = inputs[0].base
    MAX = (BASE**(ROWS*COLUMNS))**2
    
    NODES:Set[matrix] = set()
    EDGES:Dict[Tuple[int,int],List[Tuple[int,int,int]]] = {}
    END_SET = set([e.__hash__() for e in ends])

    #why the stack is a queue is a mystery to me
    q = queue.LifoQueue()
    for i in inputs:
        q.put_nowait(i)

    ok_to_add=True
    while not q.empty():
        logging.debug("Items left: " + str(q.qsize()))
        if q.qsize() > MAX:
            raise Exception("Queue size exceeded maximum squared!")

        #get the latest matrix
        p = q.get_nowait()
        NODES.add(p)
        h = p.__hash__()

        #if we're set to stop on some matrices, and we just reached one of them
        if len(END_SET) > 0 and p in END_SET:
            #stopping on "all" means we just remove this one
            if stop_criteria == 'all':
                END_SET.remove(p)
            #then check if the set is empty now
            #either that, or we're stopping on any
            if len(END_SET) == 0 or stop_criteria == 'any':
                #soft stop = don't add new nodes
                if stop_behavior == 'soft':
                    ok_to_add = False
                #hard stop = quit with what we have
                else:
                    return (NODES, EDGES)

        #for each set of 2 rows, and each valid scalar
        for r1 in range(ROWS):
            for r2 in range(ROWS):
                for s in range(1,BASE):
                    #perform the operation
                    _p = p.copy()
                    _p.AddRows(r1,r2,s)
                    
                    #add node
                    if ok_to_add and _p not in NODES:
                        q.put(_p)

                    #add edge
                    dh = _p.__hash__()
                    if include_self_transitions or not h == dh:
                        if not (h,dh) in EDGES:
                            EDGES[(h,dh)] = set([(r1,s,r2)])
                        else:
                            EDGES[(h,dh)].add(((r1,s,r2)))

    #return result
    return (NODES, EDGES)

def make_edge_desc(e:List[Tuple[int,int,int]]) -> str:
    d = ""
    for w in e:
        d += "R" + str(w[0]+1) + " += " + str(w[1]) + "*R" + str(w[2]+1) + "\\n"
    return d

def make_plantuml(path:str, starts:List[matrix], nodes, edges):
    o = "@startuml\n"
    for s in starts:
        o += f"[*] --> {s.__hash__()}\n"
    for p in nodes:
        o += f"{p.__hash__()}: {p}\n"

    for k,v in edges.items():
        o += f"{k[0]} --> {k[1]}: {make_edge_desc(v)}\n"

    o += "@enduml"
    with open(path, "w") as of:
        of.write(o)

def make_graphviz(path:str, starts:List[matrix], nodes, edges):
    dot = graphviz.Digraph(comment=f"Graph from {', '.join([str(x.__hash__()) for x in starts])}")

    for p in nodes:
        dot.node(str(p.__hash__()), str(p))
    for k,v in edges.items():
        dot.edge(str(k[0]),str(k[1]), make_edge_desc(v))

    dot.save(path)

PYTHONIC_MATRIX_RE = re.compile("\[?((?:\[\s*[a-zA-Z0-9]+\s*(?:,\s*[a-zA-Z0-9]+\s*)*\]\s*,?\s*)+)\]?")
PYTHONIC_ROW_RE = re.compile("\[(\s*[a-zA-Z0-9]+\s*(?:,\s*[a-zA-Z0-9]+\s*)*)\]")
def read_matrix(s:str, base=-1) -> matrix:
    s = s.strip()
    
    def get_int(s:str) -> int:
        return int(s) if base < 0 else int(s,base)

    #read pythonic definition
    pmm = PYTHONIC_MATRIX_RE.match(s)
    if not pmm == None:
        rows = [g.split(",") for g in PYTHONIC_ROW_RE.findall(pmm.group(1))]

    #read laytex definition
    else:
        rows = [r.split("&") for r in s.split("\\") if len(r.strip()) > 0]
    
    logging.debug(rows)
    
    m = matrix([[get_int(c) for c in r] for r in rows], base)
    
    g = itertools.groupby([len(r) for r in rows])
    if not (next(g,True) and not next(g,False)):
        raise Exception("Non-rectangular matrix provided! " + str(m))

    return m

def read_matrices(strs:List[str], base=-1, permute=False):
    outputs = []
    def add_matrices(m:matrix):
        if permute:
            for p in itertools.permutations(m.rows):
                outputs.append(matrix(p, m.base))
        else:
            outputs.append(m)

    if not strs == None:
        base_matrix = read_matrix(strs[0], base)
        add_matrices(base_matrix)

        for s in strs[1:]:
            m = read_matrix(s)
            if base_matrix.properties_eq(m):
                raise Exception("All matrices must have the same dimensions/base!")
            add_matrices(m)

    return outputs

if __name__ == "__main__":
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    handler.addFilter(logging.Filter("root"))

    root.addHandler(handler)

    parser = argparse.ArgumentParser(description="Graph all matrices reachable from the given start point(s)")
    parser.add_argument("--start", nargs="+", required=True, help="What matrices to start generation from")
    parser.add_argument("--end", nargs="*", help="What matrices are trying to be reached")
    parser.add_argument("--base", type=int, default=-1, help="What number base the matrices are in (use a value less than 0 or omit argument for automatic detection)")
    #TODO make these follow whatever operations are provided
    parser.add_argument("--permute_starts", action="store_true", help="Whether or not to permute the starting matrices (uses all allowed operations)")
    parser.add_argument("--permute_ends", action="store_true", help="Whether or not to permute the ending matrices (uses all allowed operations)")

    parser.add_argument("--ops", default="rows", choices=["rows","columns","all"], help="What operations are allowed (row operations, column operations, or all operations)")
    parser.add_argument("--stop_criteria", default="any", choices=["any", "all"], help="When to stop generating the graph (any = once ANY end graph has been reached, all = once ALL end graphs have been reached)")
    parser.add_argument("--stop_behavior", default="hard", choices=["hard", "soft"], help="What to do once the stop criteria is reached (hard = make no further changes to the graph, soft = finish processing all nodes in the queue first)")
    parser.add_argument("--include_self_transitions", action='store_true', help="Whether or not to include self transitions")
    
    parser.add_argument("--dot_out", help="Where to output a dot file to (for use with graphviz)")
    parser.add_argument("--plantuml_out", help="Where to output a plantuml file to")

    parsedArgs = parser.parse_args()

    if parsedArgs.dot_out == None and parsedArgs.plantuml_out == None:
        logging.warning("No output given!")
    elif not parsedArgs.dot_out == None:
        import graphviz
    
    STARTS :List[matrix] = []
    ENDS :List[matrix] = []
    try:
        STARTS = read_matrices(parsedArgs.start, parsedArgs.base, parsedArgs.permute_starts)
        ENDS = read_matrices(parsedArgs.end, parsedArgs.base, parsedArgs.permute_ends)
    except Exception as e:
        logging.error(e.args[0])
        quit(1)

    if len(STARTS) > 0 and len(ENDS) > 0 and not STARTS[0].properties_eq(ENDS[0]):
        logging.error("Start and End matrices must have the same dimensions/base!")
        quit(2)

    logging.info("Starting from matrices:")
    for s in STARTS:
        logging.info(str(s))
    
    if len(ENDS) > 0:
        logging.info(parsedArgs.stop_behavior + " stopping at these matrices:")
        for e in ENDS:
            logging.info(str(e))
    
    BASE = STARTS[0].base
    ROWS = len(STARTS[0].rows)
    COLUMNS = len(STARTS[0].rows[0])
    MATRICES = BASE**(ROWS*COLUMNS)
    logging.info(f"Total number of {ROWS}x{COLUMNS} matrices in base {BASE} = {MATRICES}")
    
    OPS = 0
    if parsedArgs.ops in ['rows', 'all']:
        ROW_OPS = MATRICES*(ROWS*ROWS*(BASE-1))
        logging.info(f"Total row operations = {ROW_OPS}")
        OPS += ROW_OPS
    if parsedArgs.ops in ['columns', 'all']:
        COLUMN_OPS = MATRICES*(COLUMNS*COLUMNS*(BASE-1))
        logging.info(f"Total column operations = {COLUMN_OPS}")
        OPS += COLUMN_OPS
    if parsedArgs.ops == 'all':
        logging.info(f"Total operations for this graph = {OPS}")

    NODES, EDGES = make_graph(STARTS, ENDS, parsedArgs.stop_criteria, parsedArgs.stop_behavior, parsedArgs.include_self_transitions)
    
    if len(ENDS) > 0:
        logging.info("Found a path to an end!" if any(e in NODES for e in ENDS) else "Didn't find a path to any ends...")
    
    logging.info(f"{len(NODES)} Nodes, {len(EDGES)} Edges")

    combinations_found = sum(len(x) for x in EDGES.values())
    self_transitions = sum(len(v) for k,v in EDGES.items() if k[0] == k[1])

    logging.info(f"{combinations_found} Row Operations, {self_transitions} Self Transitions, {len(EDGES) - self_transitions} Unique Transitions")

    if not parsedArgs.dot_out == None:
        make_graphviz(parsedArgs.dot_out, STARTS, NODES, EDGES)
    if not parsedArgs.plantuml_out == None:
        make_plantuml(parsedArgs.plantuml_out, STARTS, NODES, EDGES)