/* sym.c -- exact t(K) / d(K) by DFS with full sequential symmetry breaking.
 * usage: sym MODE K [seed_best]      MODE = t (general) | d (disjoint, B = [K]\A)
 * The forbidden set after steps 1..j is the union of rectangles A_i x B_i, so the state
 * is invariant under every permutation of [K] fixing each A_i and B_i setwise (acting
 * diagonally on pairs).  Hence WLOG each new A takes the lowest elements of every atom of
 * the partition generated so far, and B the lowest elements of every atom of the
 * partition refined by A.  Candidates are enumerated as count vectors over atoms. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
typedef unsigned int u32; typedef unsigned long long u64;
static int K, H, MODE, best, SEED, SHARD=0, NSH=1, SPLITD=3, SUB=0, NSUB=1, SPLITD2=5, SUB2=0, NSUB2=1, SPLITD3=6; static long long splitcnt, splitmine, subcnt, submine, sub2cnt, sub2mine; static long long nodes; static time_t T0;
static u32 cA[64], cB[64], bA[64], bB[64]; static int cN[64][32], bN[64][32];
static int matchR[32], usedR[32], adj[32], stamp;
static int tryk(int i){ u32 m=adj[i]; while(m){ int y=__builtin_ctz(m); m&=m-1;
    if(usedR[y]==stamp) continue; usedR[y]=stamp;
    if(matchR[y]<0 || tryk(matchR[y])){ matchR[y]=i; return 1; } } return 0; }
/* perfect matching A->B avoiding W; fills N (row x -> column) */
static int pm(const u32 *W, u32 A, u32 B, int *N){
  int rows[32], nr=0; u32 m=A; while(m){ int x=__builtin_ctz(m); m&=m-1; adj[nr]=B&~W[x]; rows[nr++]=x; }
  for(int i=0;i<K;i++) matchR[i]=-1;
  for(int i=0;i<nr;i++){ stamp++; if(!tryk(i)) return 0; }
  for(int y=0;y<K;y++) if(matchR[y]>=0) N[rows[matchR[y]]]=y; return 1; }
static void report(int d){
  printf("FOUND mode=%c K=%d len=%d nodes=%lld t=%lds\n", MODE, K, d, nodes, (long)(time(NULL)-T0));
  for(int i=0;i<d;i++){ printf(" step %2d: A=",i+1); for(int x=0;x<K;x++) if(bA[i]>>x&1) printf("%d,",x);
    printf(" B="); for(int y=0;y<K;y++) if(bB[i]>>y&1) printf("%d,",y);
    printf(" N="); for(int x=0;x<K;x++) if(bA[i]>>x&1) printf("%d>%d,",x,bN[i][x]); printf("\n"); }
  fflush(stdout); }
static void dfs(const u32 *W, int d);
/* atoms: elements grouped by signature, each list ascending */
typedef struct { int n, na, sz[32], el[32][32]; } Atoms;
static void atoms_of(const u64 *sig, Atoms *P){
  P->na=0; int seen[32]={0};
  for(int x=0;x<K;x++){ if(seen[x]) continue; int a=P->na++; P->sz[a]=0;
    for(int y=x;y<K;y++) if(!seen[y] && sig[y]==sig[x]){ seen[y]=1; P->el[a][P->sz[a]++]=y; } } }
static void enumB(const u32 *W, int d, u32 A, const Atoms *P, int a, int left, u32 B){
  if(a==P->na){ if(left) return; int N[32];
    if(!pm(W,A,B,N)) return;
    u32 W2[32]; memcpy(W2,W,sizeof(u32)*K); u32 m=A; while(m){ int x=__builtin_ctz(m); m&=m-1; W2[x]|=B; }
    cA[d]=A; cB[d]=B; memcpy(cN[d],N,sizeof(int)*32); dfs(W2,d+1); return; }
  int rest=0; for(int b=a+1;b<P->na;b++) rest+=P->sz[b];
  for(int c=0;c<=P->sz[a] && c<=left;c++){ if(left-c>rest) continue;
    u32 add=0; for(int i=0;i<c;i++) add|=1u<<P->el[a][i];
    enumB(W,d,A,P,a+1,left-c,B|add); } }
static void enumA(const u32 *W, int d, const u64 *sig, const Atoms *P, int a, int left, u32 A){
  if(a==P->na){ if(left) return;
    if(MODE=='d'){ u32 B=((1u<<K)-1)&~A; int N[32]; if(!pm(W,A,B,N)) return;
      u32 W2[32]; memcpy(W2,W,sizeof(u32)*K); u32 m=A; while(m){ int x=__builtin_ctz(m); m&=m-1; W2[x]|=B; }
      cA[d]=A; cB[d]=B; memcpy(cN[d],N,sizeof(int)*32); dfs(W2,d+1); return; }
    u64 s2[32]; for(int x=0;x<K;x++) s2[x]=(sig[x]<<1)|(A>>x&1);
    Atoms Q; atoms_of(s2,&Q); enumB(W,d,A,&Q,0,H,0); return; }
  int rest=0; for(int b=a+1;b<P->na;b++) rest+=P->sz[b];
  for(int c=0;c<=P->sz[a] && c<=left;c++){ if(left-c>rest) continue;
    u32 add=0; for(int i=0;i<c;i++) add|=1u<<P->el[a][i];
    enumA(W,d,sig,P,a+1,left-c,A|add); } }
static void dfs(const u32 *W, int d){
  if(NSH>1 && d==SPLITD){ if((splitcnt++ % NSH)!=SHARD) return; splitmine++; }
  if(NSUB>1 && d==SPLITD2){ if((subcnt++ % NSUB)!=SUB) return; submine++; }   /* second-level split inside one shard */
  if(NSUB2>1 && d==SPLITD3){ if((sub2cnt++ % NSUB2)!=SUB2) return; sub2mine++; }   /* third-level split */
  nodes++;
  if((nodes & ((1LL<<28)-1))==0){ fprintf(stderr,"progress nodes=%lld t=%lds best=%d\n",nodes,(long)(time(NULL)-T0),best); fflush(stderr); }
  if(d>best){ best=d; memcpy(bA,cA,sizeof(u32)*d); memcpy(bB,cB,sizeof(u32)*d);
    memcpy(bN,cN,sizeof(int)*32*d); report(d); }
  long F=0; for(int x=0;x<K;x++) F+=K-__builtin_popcount(W[x]);
  if(d + F/H <= (d<(NSUB2>1?SPLITD3:(NSUB>1?SPLITD2:SPLITD)) ? SEED : best)) return;  /* above the split only the fixed seed prunes, so shards see identical prefixes */               /* every step forbids >= H free cells */
  u64 sig[32]; for(int x=0;x<K;x++){ u64 g=0; for(int i=0;i<d;i++){ g=(g<<1)|(cA[i]>>x&1); if(MODE=='t') g=(g<<1)|(cB[i]>>x&1); } sig[x]=g; }
  Atoms P; atoms_of(sig,&P); enumA(W,d,sig,&P,0,H,0); }
int main(int argc,char**argv){
  if(argc<3){ fprintf(stderr,"usage: sym t|d K [seed] [shard nshards splitd [sub nsub splitd2 [sub2 nsub2 splitd3]]]\n"); return 2; }
  MODE=argv[1][0]; K=atoi(argv[2]); H=K/2; best=(argc>3)?atoi(argv[3]):0; SEED=best;
  if(argc>6){ SHARD=atoi(argv[4]); NSH=atoi(argv[5]); SPLITD=atoi(argv[6]); }
  if(argc>9){ SUB=atoi(argv[7]); NSUB=atoi(argv[8]); SPLITD2=atoi(argv[9]); }
  if(argc>12){ SUB2=atoi(argv[10]); NSUB2=atoi(argv[11]); SPLITD3=atoi(argv[12]); } T0=time(NULL);
  if(K<2||K>30||(K&1)||(MODE!='t'&&MODE!='d')){ fprintf(stderr,"bad args\n"); return 2; }
  u32 W[32]={0}; dfs(W,0);
  printf("DONE mode=%c K=%d value=%d seed=%d shard=%d/%d splitd=%d splitcnt=%lld mine=%lld sub=%d/%d splitd2=%d subcnt=%lld submine=%lld sub2=%d/%d splitd3=%d sub2cnt=%lld sub2mine=%lld nodes=%lld t=%lds\n", MODE,K,best,SEED,SHARD,NSH,SPLITD,splitcnt,splitmine,SUB,NSUB,SPLITD2,subcnt,submine,SUB2,NSUB2,SPLITD3,sub2cnt,sub2mine,nodes,(long)(time(NULL)-T0));
  return 0; }
