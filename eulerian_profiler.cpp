#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#include <iostream>
#include <vector>
#include <list>
#include <chrono>
#include <cmath>
#include <map>
#include <set>
#include <algorithm>

using namespace std;
using namespace std::chrono;

// ---------------------------------------------------------------------------
// Data types
// ---------------------------------------------------------------------------
struct Point {
    int y, x;
    bool operator<(const Point& o)  const { return y != o.y ? y < o.y : x < o.x; }
    bool operator==(const Point& o) const { return y == o.y && x == o.x; }
    bool operator!=(const Point& o) const { return !(*this == o); }
};

struct Edge {
    Point u, v;
    vector<Point> path;
    int id;
};

struct Graph {
    map<Point, vector<Edge>> adj;
    int edge_count = 0;

    void add_edge(Point u, Point v, const vector<Point>& path) {
        int eid = edge_count++;
        adj[u].push_back({u, v, path, eid});
        vector<Point> rpath(path.rbegin(), path.rend());
        adj[v].push_back({v, u, rpath, eid});
    }
};

// ---------------------------------------------------------------------------
// 1. Image Processing: binarize + Zhang-Suen skeletonization
// ---------------------------------------------------------------------------
static int nbr_count(const vector<vector<int>>& img, int y, int x, int H, int W) {
    int c = 0;
    for (int dy = -1; dy <= 1; dy++)
        for (int dx = -1; dx <= 1; dx++)
            if ((dy || dx) && y+dy>=0 && y+dy<H && x+dx>=0 && x+dx<W)
                c += img[y+dy][x+dx];
    return c;
}

static int transitions(const vector<vector<int>>& img, int y, int x, int H, int W) {
    // clockwise sequence: top, top-right, right, bottom-right, bottom, bottom-left, left, top-left
    static const int DY[8] = {-1,-1,0,1,1,1,0,-1};
    static const int DX[8] = {0,1,1,1,0,-1,-1,-1};
    int p[8];
    for (int i = 0; i < 8; i++) {
        int ny = y+DY[i], nx = x+DX[i];
        p[i] = (ny>=0&&ny<H&&nx>=0&&nx<W) ? img[ny][nx] : 0;
    }
    int t = 0;
    for (int i = 0; i < 8; i++) t += (!p[i] && p[(i+1)%8]);
    return t;
}

static vector<vector<int>> zhang_suen(vector<vector<int>> img, int H, int W) {
    bool changed = true;
    vector<vector<int>> mark(H, vector<int>(W, 0));
    while (changed) {
        changed = false;
        // Sub-iteration 1
        for (int y = 1; y < H-1; y++) for (int x = 1; x < W-1; x++) {
            if (!img[y][x]) continue;
            int B = nbr_count(img,y,x,H,W), A = transitions(img,y,x,H,W);
            int p2=img[y-1][x], p4=img[y][x+1], p6=img[y+1][x], p8=img[y][x-1];
            if (B>=2&&B<=6&&A==1&&!(p2*p4*p6)&&!(p4*p6*p8)) { mark[y][x]=1; changed=true; }
        }
        for (int y=0;y<H;y++) for (int x=0;x<W;x++) if (mark[y][x]) { img[y][x]=0; mark[y][x]=0; }
        // Sub-iteration 2
        for (int y = 1; y < H-1; y++) for (int x = 1; x < W-1; x++) {
            if (!img[y][x]) continue;
            int B = nbr_count(img,y,x,H,W), A = transitions(img,y,x,H,W);
            int p2=img[y-1][x], p4=img[y][x+1], p6=img[y+1][x], p8=img[y][x-1];
            if (B>=2&&B<=6&&A==1&&!(p2*p4*p8)&&!(p2*p6*p8)) { mark[y][x]=1; changed=true; }
        }
        for (int y=0;y<H;y++) for (int x=0;x<W;x++) if (mark[y][x]) { img[y][x]=0; mark[y][x]=0; }
    }
    return img;
}

// ---------------------------------------------------------------------------
// 2. Graph Builder
// ---------------------------------------------------------------------------
static const int DY8[8] = {-1,-1,-1,0,0,1,1,1};
static const int DX8[8] = {-1,0,1,-1,1,-1,0,1};

Graph build_graph(const vector<vector<int>>& sk, int H, int W) {
    Graph g;
    set<Point> nodes;
    vector<Point> pixels;

    for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) {
        if (!sk[y][x]) continue;
        pixels.push_back({y,x});
        int n = nbr_count(sk,y,x,H,W);
        if (n == 1 || n > 2) nodes.insert({y,x});
    }
    if (nodes.empty() && !pixels.empty()) nodes.insert(pixels[0]);

    set<Point> vis;
    for (auto node : nodes) {
        for (int d = 0; d < 8; d++) {
            int ny = node.y+DY8[d], nx = node.x+DX8[d];
            if (ny<0||ny>=H||nx<0||nx>=W||!sk[ny][nx]) continue;
            Point nb = {ny,nx};
            if (vis.count(nb)) continue;

            vector<Point> path = {node, nb};
            Point curr = nb, prev = node;
            while (!nodes.count(curr)) {
                vis.insert(curr);
                Point nxt = {-1,-1};
                for (int j = 0; j < 8; j++) {
                    int cy=curr.y+DY8[j], cx=curr.x+DX8[j];
                    Point c={cy,cx};
                    if (cy>=0&&cy<H&&cx>=0&&cx<W&&sk[cy][cx]&&c!=prev) { nxt=c; break; }
                }
                if (nxt.y < 0) break;
                prev=curr; curr=nxt; path.push_back(curr);
            }
            if (nodes.count(curr)) g.add_edge(node, curr, path);
        }
    }
    return g;
}

// ---------------------------------------------------------------------------
// 3. Eulerian Logic  — only apply double-wall when truly needed
// ---------------------------------------------------------------------------
Graph make_eulerian(Graph g) {
    int odd = 0;
    for (auto& p : g.adj) if (p.second.size() % 2 != 0) odd++;
    if (odd <= 2) return g; // already Eulerian or semi-Eulerian

    Graph fg;
    for (auto& p : g.adj)
        for (auto& e : p.second)
            if (e.u < e.v) { fg.add_edge(e.u,e.v,e.path); fg.add_edge(e.u,e.v,e.path); }
    return fg;
}

// ---------------------------------------------------------------------------
// 4. Path Generator — stack-based Hierholzer + angular preference  O(E·deg)
// ---------------------------------------------------------------------------
static Point get_tangent(const vector<Point>& path, bool from_start) {
    if (path.size() < 2) return {0,0};
    int idx = min((int)path.size()-1, 5);
    return from_start
        ? Point{path[idx].y - path[0].y,   path[idx].x - path[0].x}
        : Point{path.back().y - path[path.size()-1-idx].y,
                path.back().x - path[path.size()-1-idx].x};
}

static double angle_score(Point v1, Point v2) {
    double dot  = v1.y*v2.y + v1.x*v2.x;
    double m1   = sqrt(v1.y*v1.y + v1.x*v1.x);
    double m2   = sqrt(v2.y*v2.y + v2.x*v2.x);
    return (m1>0&&m2>0) ? dot/(m1*m2) : 0.0;
}

// Stack-based Hierholzer — each edge pushed/popped exactly once → O(E) stack ops.
// Angular scoring per step → O(deg) per step. Total: O(E * deg_max).
// Per-node cursors prevent re-scanning visited edges from index 0 each time.
vector<Point> angular_walker(Graph& g) {
    vector<Point> full_path;
    if (g.adj.empty()) return full_path;

    // Per-node cursor: index of first *possibly* unvisited edge in adj list.
    map<Point, int> cursor;
    for (auto& p : g.adj) cursor[p.first] = 0;

    set<int> visited;

    // Prefer odd-degree start node for a path; any node for a circuit.
    Point start = g.adj.begin()->first;
    for (auto& p : g.adj) if (p.second.size()%2!=0) { start=p.first; break; }

    struct Frame { Point node; Point in_vec; };
    vector<Frame> stk;
    vector<Edge>  edge_stk; // parallel to stk (offset 1): edge that brought us here

    stk.push_back({start, {0,0}});
    list<Edge> circuit;

    while (!stk.empty()) {
        Point curr   = stk.back().node;
        Point in_vec = stk.back().in_vec;
        auto& adj    = g.adj[curr];
        int&  cur    = cursor[curr];

        // Advance cursor past already-visited edges
        while (cur < (int)adj.size() && visited.count(adj[cur].id)) cur++;

        if (cur >= (int)adj.size()) {
            // No more edges from curr — unwind: record edge in circuit and pop
            stk.pop_back();
            if (!edge_stk.empty()) { circuit.push_front(edge_stk.back()); edge_stk.pop_back(); }
            continue;
        }

        // Find best-scoring unvisited edge via angular preference
        int    best_i = cur;
        double best_s = -2.0;
        for (int i = cur; i < (int)adj.size(); i++) {
            if (visited.count(adj[i].id)) continue;
            Point out = get_tangent(adj[i].path, true);
            double s  = (in_vec.y||in_vec.x) ? angle_score(in_vec, out) : 0.0;
            if (s > best_s) { best_s=s; best_i=i; }
        }

        // Swap chosen edge to cursor slot so the cursor advance will skip it
        swap(adj[best_i], adj[cur]);
        Edge chosen = adj[cur];
        cur++;

        visited.insert(chosen.id);
        Point exit_v = get_tangent(chosen.path, false);
        edge_stk.push_back(chosen);
        stk.push_back({chosen.v, {exit_v.y, exit_v.x}});
    }

    bool first = true;
    for (auto& e : circuit) {
        if (first) { full_path.insert(full_path.end(), e.path.begin(), e.path.end()); first=false; }
        else        { full_path.insert(full_path.end(), e.path.begin()+1, e.path.end()); }
    }
    return full_path;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
int main(int argc, char** argv) {
    if (argc < 2) { cerr << "Usage: " << argv[0] << " <image>\n"; return 1; }

    auto T0 = high_resolution_clock::now();

    // Load
    int W, H, ch;
    unsigned char* raw = stbi_load(argv[1], &W, &H, &ch, 1);
    if (!raw) { cerr << "Cannot load " << argv[1] << "\n"; return 1; }

    vector<vector<int>> img(H, vector<int>(W));
    for (int y=0;y<H;y++) for (int x=0;x<W;x++) img[y][x] = raw[y*W+x] < 128 ? 1 : 0;
    stbi_image_free(raw);

    cout << "--- Profiling Information ---\n";
    cout << "Image Size: " << W << " x " << H << "\n";

    // T1: Skeletonize
    auto T1s = high_resolution_clock::now();
    img = zhang_suen(img, H, W);
    auto T1e = high_resolution_clock::now();
    int skel_px = 0;
    for (int y=0;y<H;y++) for (int x=0;x<W;x++) skel_px += img[y][x];
    cout << "Skeleton Pixels: " << skel_px << "\n";

    // T2: Build graph
    auto T2s = high_resolution_clock::now();
    Graph g = build_graph(img, H, W);
    auto T2e = high_resolution_clock::now();
    cout << "Raw Graph Edges: " << g.edge_count << "\n";

    // T3: Eulerian transform
    auto T3s = high_resolution_clock::now();
    Graph ge = make_eulerian(g);
    auto T3e = high_resolution_clock::now();
    cout << "Eulerian Graph Edges: " << ge.edge_count << "\n";

    // T4: Path generation
    auto T4s = high_resolution_clock::now();
    vector<Point> path = angular_walker(ge);
    auto T4e = high_resolution_clock::now();

    auto T_end = high_resolution_clock::now();

    cout << "Generated Path Length: " << path.size() << " pixels\n";
    cout << "-----------------------------\n";
    cout << "Skeletonization Time : " << duration_cast<milliseconds>(T1e-T1s).count() << " ms\n";
    cout << "Build Graph Time     : " << duration_cast<milliseconds>(T2e-T2s).count() << " ms\n";
    cout << "Eulerian Logic Time  : " << duration_cast<milliseconds>(T3e-T3s).count() << " ms\n";
    cout << "Path Gen Time        : " << duration_cast<milliseconds>(T4e-T4s).count() << " ms\n";
    cout << "Total Time           : " << duration_cast<milliseconds>(T_end-T0).count()  << " ms\n";
    return 0;
}
