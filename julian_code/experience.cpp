#include "common.hpp"
#include "vector"
#include "map"
#include "limits"
#include "omp.h"
#include "lbfgs.h"

#include "experience.hpp"
using namespace std;

double square(double x)
{
  return x*x;
}

/// Smoothness prior
double gpp(double x, double y, double lambda2)
{
  return lambda2/2.0*square(x-y);
}

/// Gradient of smoothness prior
double gpd(double x, double y, double lambda2, int which)
{
  if (which == 0)
    return lambda2*(x-y);
  else
    return -lambda2*(x-y);
}

/// Collapse all parameters to a vector (for lbfgs)
int expCorpus::putG(double* g, double alpha, double* effectE, double** beerD, double** userD, double* beerBias, double* userBias, double*** beerLatent, double*** userLatent)
{
  int ind = 0;
  g[ind++] = alpha;

  for (int e = 0; e < E; e ++)
    g[ind++] = effectE[e];

  for (int b = 0; b < nBeers; b ++)
    for (int d = 0; d < E; d ++)
      g[ind++] = beerD[b][d];

  for (int u = 0; u < nUsers; u ++)
    for (int d = 0; d < E; d ++)
      g[ind++] = userD[u][d];

  for (int b = 0; b < nBeers; b ++)
    g[ind++] = beerBias[b];
  for (int u = 0; u < nUsers; u ++)
    g[ind++] = userBias[u];
  
  for (int b = 0; b < nBeers; b ++)
    for (int e = 0; e < E; e ++)
      for (int k = 0; k < K; k ++)
        g[ind++] = beerLatent[b][e][k];
  for (int u = 0; u < nUsers; u ++)
    for (int e = 0; e < E; e ++)
      for (int k = 0; k < K; k ++)
        g[ind++] = userLatent[u][e][k];

  if (ind != NW)
  {
    printf("Got incorrect index at line %d\n", __LINE__);
    exit(1);
  }
  return ind;
}

/// Recover all parameters from a vector (from lbfgs)
int expCorpus::getG(double* g, double* alpha, double** effectE, double*** beerD, double*** userD, double** beerBias, double** userBias, double**** beerLatent, double**** userLatent, bool init)
{
  int ind = 0;
  *alpha = g[ind++];

  if (init) *effectE = new double [E];
  for (int e = 0; e < E; e ++)
    (*effectE)[e] = g[ind++];
  
  if (init) *beerD = new double* [nBeers];
  for (int b = 0; b < nBeers; b ++)
  {
    if (init) (*beerD)[b] = new double [E];
    for (int e = 0; e < E; e ++)
      (*beerD)[b][e] = g[ind++];
  }
  
  if (init) *userD = new double* [nUsers];
  for (int u = 0; u < nUsers; u ++)
  {
    if (init) (*userD)[u] = new double [E];
    for (int e = 0; e < E; e ++)
      (*userD)[u][e] = g[ind++];
  }

  if (init) *beerBias = new double [nBeers];
  for (int b = 0; b < nBeers; b ++)
    (*beerBias)[b] = g[ind++];
  if (init) *userBias = new double [nUsers];
  for (int u = 0; u < nUsers; u ++)
    (*userBias)[u] = g[ind++];
  
  if (init) *beerLatent = new double** [nBeers];
  for (int b = 0; b < nBeers; b ++)
  {
    if (init) (*beerLatent)[b] = new double* [E];
    for (int e = 0; e < E; e ++)
    {
      if (init) (*beerLatent)[b][e] = new double [K];
      for (int k = 0; k < K; k ++)
        (*beerLatent)[b][e][k] = g[ind++];
    }
  }
  if (init) *userLatent = new double** [nUsers];
  for (int u = 0; u < nUsers; u ++)
  {
    if (init) (*userLatent)[u] = new double* [E];
    for (int e = 0; e < E; e ++)
    {
      if (init) (*userLatent)[u][e] = new double [K];
      for (int k = 0; k < K; k ++)
        (*userLatent)[u][e][k] = g[ind++];
    }
  }

  if (ind != NW)
  {
    printf("Got incorrect index at line %d\n", __LINE__);
    exit(1);
  }
  return ind;
}

/// Free all parameter vectors
void expCorpus::clearG(double* alpha, double** effectE, double*** beerD, double*** userD, double** beerBias, double** userBias, double**** beerLatent, double**** userLatent)
{
  delete [] (*effectE);
  for (int b = 0; b < nBeers; b ++)
    delete [] (*beerD)[b];
  for (int u = 0; u < nUsers; u ++)
    delete [] (*userD)[u];
  delete [] *(beerD);
  delete [] *(userD);

  delete [] *(beerBias);
  delete [] *(userBias);
  
  for (int b = 0; b < nBeers; b ++)
  {
    for (int e = 0; e < E; e ++)
      delete [] (*beerLatent)[b][e];
    delete [] (*beerLatent)[b];
  }
  delete [] (*beerLatent);
  for (int u = 0; u < nUsers; u ++)
  {
    for (int e = 0; e < E; e ++)
      delete [] (*userLatent)[u][e];
    delete [] (*userLatent)[u];
  }
  delete [] (*userLatent);
}

/// Compute gradient for the current parameter values
static lbfgsfloatval_t evaluate(void *instance, const lbfgsfloatval_t *x, lbfgsfloatval_t *g, const int n, const lbfgsfloatval_t step)
{
  expCorpus* ec = (expCorpus*) instance;

  double* xx = new double [ec->NW];
  for (int i = 0; i < ec->NW; i ++)
    xx[i] = x[i];
  ec->getG(xx, &(ec->alpha), &(ec->effectE), &(ec->beerD), &(ec->userD), &(ec->beerBias), &(ec->userBias), &(ec->beerLatent), &(ec->userLatent), false);
  delete [] xx;

  double* grad = new double [ec->NW];
  ec->dl(grad);
  for (int i = 0; i < ec->NW; i ++)
    g[i] = grad[i];
  delete [] grad;

  lbfgsfloatval_t fx = ec->lsq(true);
  return fx;
}

static int progress(void *instance, const lbfgsfloatval_t *x, const lbfgsfloatval_t *g, const lbfgsfloatval_t fx, const lbfgsfloatval_t xnorm, const lbfgsfloatval_t gnorm, const lbfgsfloatval_t step, int n, int k, int ls)
{
  printf(".");
  fflush(stdout);
  return 0;
}

/// Inner product
inline double inp(double* v1, double* v2, int K)
{
  double res = 0;
  for (int k = 0; k < K; k ++)
    res += v1[k] * v2[k];
  return res;
}

/// Prediction for a particular rating given current parameters
double expCorpus::prediction(int experience, vote* vi)
{
  return alpha +
         beerBias[vi->item] + 
         userBias[vi->user] +
         effectE[experience] +
         beerD[vi->item][experience] + 
         userD[vi->user][experience] + 
         inp(beerLatent[vi->item][experience], userLatent[vi->user][experience], K);
}

/// Given the ratings and degrees of difficulty, predict the most likely experience levels using dynamic programming
int expCorpus::predictExpLevel()
{
  int changed = 0;
  for (int u = 0; u < corp->nUsers; u ++)
  {
    vector<vote*>* vs = &(votesPerUser[u]);
    int nr = vs->size();
    if (nr == 0) continue;

    double** best = new double* [nr];
    int** dir = new int* [nr];

    for (int r = 0; r < nr; r ++)
    {
      best[r] = new double [E];
      dir[r] = new int [E];
    }

    vote* firstvote = vs->at(0);
    for (int e = 0; e < E; e ++)
    {
      best[0][e] = square(prediction(e, firstvote) - firstvote->value);
      dir[0][e] = 0;
    }

    for (int r = 1; r < nr; r ++)
    {
      vote* vi = vs->at(r);
      best[r][0] = square(prediction(0, vi) - vi->value) + best[r-1][0];
      dir[r][0] = 0;
    }

    for (int r = 1; r < nr; r ++)
    {
      vote* vi = vs->at(r);
      for (int e = 1; e < E; e ++)
      {
        double scoreHere = square(prediction(e, vi) - vi->value);
        double score0 = best[r-1][e];
        double score1 = best[r-1][e-1];
        if (score0 < score1)
        {
          best[r][e] = scoreHere + score0;
          dir[r][e] = 0;
        }
        else
        {
          best[r][e] = scoreHere + score1;
          dir[r][e] = -1;
        }
      }
    }

    int bestStart = -1;
    double bestScore = numeric_limits<double>::max();
    for (int e = 0; e < E; e ++)
    {
      if (best[nr-1][e] < bestScore)
      {
        bestStart = e;
        bestScore = best[nr-1][e];
      }
    }

    int r = nr - 1;
    int current = bestStart;
    if (userExperience[vs->at(r)] != current) changed ++;
    userExperience[vs->at(r)] = current;
    while (r > 0)
    {
      if (dir[r][current] == -1) current -= 1;
      r -= 1;
      if (userExperience[vs->at(r)] != current) changed ++;
      userExperience[vs->at(r)] = current;
    }

    for (int r = 0; r < nr; r ++)
    {
      delete [] best[r];
      delete [] dir[r];
    }
    delete [] best;
    delete [] dir;
  }

  return changed;
}

/// Same as the function above, but operates at the level of communities, rather than individual users
int expCorpus::predictExpLevelForCommunity()
{
  int changed = 0;

  vector<vote*>* vs = &trainVotes;
  int nr = vs->size();

  double** best = new double* [nr];
  int** dir = new int* [nr];

  for (int r = 0; r < nr; r ++)
  {
    best[r] = new double [E];
    dir[r] = new int [E];
  }

  vote* firstvote = vs->at(0);
  for (int e = 0; e < E; e ++)
  {
    best[0][e] = square(prediction(e, firstvote) - firstvote->value);
    dir[0][e] = 0;
  }

  for (int r = 1; r < nr; r ++)
  {
    vote* vi = vs->at(r);
    best[r][0] = square(prediction(0, vi) - vi->value) + best[r-1][0];
    dir[r][0] = 0;
  }

  for (int r = 1; r < nr; r ++)
  {
    vote* vi = vs->at(r);
    for (int e = 1; e < E; e ++)
    {
      double scoreHere = square(prediction(e, vi) - vi->value);
      best[r][e] = numeric_limits<double>::max(); 
      for (int s = 0; s <= 1; s ++)
      {
        double scoreS = best[r-1][e-s];
        if (scoreHere + scoreS < best[r][e])
        {
          best[r][e] = scoreHere + scoreS;
          dir[r][e] = -s;
        }
      }
    }
  }

  int bestStart = -1;
  double bestScore = numeric_limits<double>::max();
  for (int e = 0; e < E; e ++)
  {
    if (best[nr-1][e] < bestScore)
    {
      bestStart = e;
      bestScore = best[nr-1][e];
    }
  }

  int r = nr - 1;
  int current = bestStart;
  if (userExperience[vs->at(r)] != current) changed ++;
  userExperience[vs->at(r)] = current;
  while (r > 0)
  {
    current += dir[r][current];
    r -= 1;
    if (userExperience[vs->at(r)] != current) changed ++;
    userExperience[vs->at(r)] = current;
  }

  for (int r = 0; r < nr; r ++)
  {
    delete [] best[r];
    delete [] dir[r];
  }
  delete [] best;
  delete [] dir;

  return changed;
}

/// Derivative of log-likelihood
void expCorpus::dl(double* grad)
{
  int ncores = omp_get_max_threads();
  
  double** dgCore = new double* [ncores];
  
  double* dalphaCore = new double [ncores];
  double** deffectECore = new double* [ncores];
  double*** dbeerDCore = new double** [ncores];
  double*** duserDCore = new double** [ncores];
  double** dbeerBiasCore = new double* [ncores];
  double** duserBiasCore = new double* [ncores];
  double**** dbeerLatentCore = new double*** [ncores];
  double**** duserLatentCore = new double*** [ncores];

  for (int core = 0; core < ncores; core ++)
  {
    dgCore[core] = new double [NW];
    for (int i = 0; i < NW; i ++)
      dgCore[core][i] = 0;

    getG(dgCore[core], &(dalphaCore[core]), &(deffectECore[core]), &(dbeerDCore[core]), &(duserDCore[core]), &(dbeerBiasCore[core]), &(duserBiasCore[core]), &(dbeerLatentCore[core]), &(duserLatentCore[core]), true);
  }

#pragma omp parallel for
  for (int x = 0; x < (int) trainVotes.size(); x ++)
  {
    vote* vi = trainVotes[x];
    int core = omp_get_thread_num();
    int ue = userExperience[vi];
    
    double p = prediction(ue, vi);
    double l = p - vi->value;

    deffectECore[core][ue] += 2*l;
    
    duserDCore[core][vi->user][ue] += 2*l;
    dbeerDCore[core][vi->item][ue] += 2*l;
    
    for (int k = 0; k < K; k ++)
    {
      dbeerLatentCore[core][vi->item][ue][k] += 2*l*userLatent[vi->user][ue][k];
      duserLatentCore[core][vi->user][ue][k] += 2*l*beerLatent[vi->item][ue][k];
    }
  }

  double* x = new double [NW];
  putG(x, alpha, effectE, beerD, userD, beerBias, userBias, beerLatent, userLatent);

  for (int i = 0; i < NW; i ++)
    grad[i] = 0;
  for (int i = 1; i < NW - nBeers - nUsers; i ++)
    grad[i] = lambda1*x[i];
  delete [] x;

  for (int y = 1; y < E; y ++)
  {
    deffectECore[0][y - 1] += gpd(effectE[y - 1], effectE[y], lambda2, 0);
    deffectECore[0][y] += gpd(effectE[y - 1], effectE[y], lambda2, 1);
  }

  for (int b = 0; b < nBeers; b ++)
    for (int e = 1; e < E; e ++)
    {
      dbeerDCore[0][b][e - 1] += gpd(beerD[b][e - 1], beerD[b][e], lambda2, 0);
      dbeerDCore[0][b][e] += gpd(beerD[b][e - 1], beerD[b][e], lambda2, 1);
    }

  for (int u = 0; u < nUsers; u ++)
    for (int e = 1; e < E; e ++)
    {
      duserDCore[0][u][e - 1] += gpd(userD[u][e - 1], userD[u][e], lambda2, 0);
      duserDCore[0][u][e] += gpd(userD[u][e - 1], userD[u][e], lambda2, 1);
    }

  for (int b = 0; b < nBeers; b ++)
    for (int k = 0; k < K; k ++)
      for (int e = 1; e < E; e ++)
      {
        dbeerLatentCore[0][b][e - 1][k] += gpd(beerLatent[b][e - 1][k], beerLatent[b][e][k], lambda2, 0);
        dbeerLatentCore[0][b][e][k] += gpd(beerLatent[b][e - 1][k], beerLatent[b][e][k], lambda2, 1);
      }
  for (int u = 0; u < nUsers; u ++)
    for (int k = 0; k < K; k ++)
      for (int e = 1; e < E; e ++)
      {
        duserLatentCore[0][u][e - 1][k] += gpd(userLatent[u][e - 1][k], userLatent[u][e][k], lambda2, 0);
        duserLatentCore[0][u][e][k] += gpd(userLatent[u][e - 1][k], userLatent[u][e][k], lambda2, 1);
      }

  for (int core = 0; core < ncores; core ++)
  {
    putG(dgCore[core], dalphaCore[core], deffectECore[core], dbeerDCore[core], duserDCore[core], dbeerBiasCore[core], duserBiasCore[core], dbeerLatentCore[core], duserLatentCore[core]);

    for (int i = 0; i < NW; i ++)
      grad[i] += dgCore[core][i];

    clearG(&(dalphaCore[core]), &(deffectECore[core]), &(dbeerDCore[core]), &(duserDCore[core]), &(dbeerBiasCore[core]), &(duserBiasCore[core]), &(dbeerLatentCore[core]), &(duserLatentCore[core]));
  }

  delete [] dalphaCore;
  delete [] deffectECore;
  delete [] dbeerDCore;
  delete [] duserDCore;
  delete [] dbeerBiasCore;
  delete [] duserBiasCore;
  delete [] dbeerLatentCore;
  delete [] duserLatentCore;

  for (int core = 0; core < ncores; core ++)
    delete [] dgCore[core];
  delete [] dgCore;
}

/// Energy (according to least-squares criterion)
double expCorpus::lsq(bool addreg)
{
  int ncores = omp_get_max_threads();
  double* resCore = new double [ncores];
  for (int i = 0; i < ncores; i ++)
    resCore[i] = 0;

  for (int x = 0; x < (int) trainVotes.size(); x ++)
  {
    vote* vi = trainVotes[x];
    resCore[omp_get_thread_num()] += square(prediction(userExperience[vi], vi) - vi->value);
  }

  double res = 0;
  for (int i = 0; i < ncores; i ++)
    res += resCore[i];
  delete [] resCore;

  if (addreg)
  {
    double* x = new double [NW];
    putG(x, alpha, effectE, beerD, userD, beerBias, userBias, beerLatent, userLatent);

    for (int i = 1; i < NW - nBeers - nUsers; i ++)
      res += (lambda1/2)*x[i]*x[i];
    delete [] x;

    for (int y = 1; y < E; y ++)
      res += gpp(effectE[y - 1], effectE[y], lambda2);

    for (int b = 0; b < nBeers; b ++)
      for (int e = 1; e < E; e ++)
        res += gpp(beerD[b][e - 1], beerD[b][e], lambda2);
    for (int u = 0; u < nUsers; u ++)
      for (int e = 1; e < E; e ++)
        res += gpp(userD[u][e - 1], userD[u][e], lambda2);
    
    for (int b = 0; b < nBeers; b ++)
      for (int k = 0; k < K; k ++)
        for (int e = 1; e < E; e ++)
          res += gpp(beerLatent[b][e - 1][k], beerLatent[b][e][k], lambda2);
    for (int u = 0; u < nUsers; u ++)
      for (int k = 0; k < K; k ++)
        for (int e = 1; e < E; e ++)
          res += gpp(userLatent[u][e - 1][k], userLatent[u][e][k], lambda2);
  }

  return res;
}

/// Train the model
void expCorpus::train(int emIterations, int gradIterations)
{
  for (int emi = 0; emi < emIterations; emi ++)
  {
    double ll_prev = lsq(true);

    lbfgsfloatval_t fx = 0;
    lbfgsfloatval_t* x = lbfgs_malloc(NW);

    double* xx = new double [NW];
    putG(xx, alpha, effectE, beerD, userD, beerBias, userBias, beerLatent, userLatent);
    for (int i = 0; i < NW; i ++)
      x[i] = xx[i];
    delete [] xx;

    lbfgs_parameter_t param;
    lbfgs_parameter_init(&param);
    param.max_iterations = gradIterations;
    param.epsilon = 1e-2;
    param.delta = 1e-2;
    lbfgs(NW, x, &fx, evaluate, progress, (void*) this, &param);
    printf("\nenergy after gradient step = %f\n", fx);
    lbfgs_free(x);
    ll_prev = fx;

    if (trainMode == RECOMMENDER or trainMode == STATIC_USER_EVOLUTION or trainMode == STATIC_COMMUNITY_EVOLUTION)
    {
      printf("Error on validation set = %f\n", testError(true, NULL));
      printf("Error on test set = %f\n", testError(false, NULL));

      break;
    }

    double eAv = 0;
    for (int e = 0; e < E; e ++)
      eAv += effectE[e];
    for (int e = 0; e < E; e ++)
      effectE[e] -= eAv/E;
    alpha += eAv/E;

    for (int u = 0; u < nUsers; u ++)
    {
      double uAv = 0;
      for (int e = 0; e < E; e ++)
        uAv += userD[u][e];
      for (int e = 0; e < E; e ++)
        userD[u][e] -= uAv/E;
      userBias[u] += uAv/E;
    }
    for (int b = 0; b < nBeers; b ++)
    {
      double bAv = 0;
      for (int e = 0; e < E; e ++)
        bAv += beerD[b][e];
      for (int e = 0; e < E; e ++)
        beerD[b][e] -= bAv/E;
      beerBias[b] += bAv/E;
    }

    int changed = 0;
    if (trainMode == LEARNED_USER_EVOLUTION)
      changed = predictExpLevel();
    else if (trainMode == LEARNED_COMMUNITY_EVOLUTION)
      changed = predictExpLevelForCommunity();
    if (not changed) break;

    double ll_ = lsq(true);
    printf("energy after experience step = %f\n", ll_);

    printf("Error on validation set = %f\n", testError(true, NULL));
    printf("Error on test set = %f\n", testError(false, NULL));

    if (ll_ > ll_prev)
    {
      printf("Least-squares increased in experience step.\n");
      break;
    }
    ll_prev = ll_;
    printf(".");
    fflush(stdout);
  }
}

/// Compute the testing error for a model
double expCorpus::testError(bool validate, FILE* outFile)
{
  double error = 0;

  int count = 0;
  for (int user = 0; user < nUsers; user ++)
  {
    vector<vote*>* userVotes = &validVotesPerUser[user];
    if (!validate)
      userVotes = &testVotesPerUser[user];

    if (votesPerUser[user].size() == 0 or userVotes->size() == 0) continue;
    
    for (vector<vote*>::iterator it = userVotes->begin(); it != userVotes->end(); it ++)
    {
      vote* vi = *it;
      int ue = userExperience[nearestVote[vi]];
      double p = prediction(ue, vi);
      if (outFile)
        fprintf(outFile, "%s %s %d %f %f\n", corp->rUserIds[user].c_str(), corp->rBeerIds[vi->item].c_str(), ue, vi->value, p);
      error += square(p - vi->value);
      count ++;
    }
  }

  return error / count;
}

/// Copy the parameters of one model to another. This function is used after training a "standard" recommender system, so that the experience-based recommender system initially uses the same parameters for every experience level.
void copyParameters(expCorpus* ec1, expCorpus* ec)
{
  ec->alpha = ec1->alpha;
  for (int k = 0; k < ec->E; k ++)
  {
    ec->effectE[k] = ec1->effectE[0];
    for (int u = 0; u < ec->nUsers; u ++)
      ec->userD[u][k] = ec1->userD[u][0];
    for (int b = 0; b < ec->nBeers; b ++)
      ec->beerD[b][k] = ec1->beerD[b][0];
  }
  for (int u = 0; u < ec->nUsers; u ++)
    ec->userBias[u] = ec1->userBias[u];
  for (int b = 0; b < ec->nBeers; b ++)
    ec->beerBias[b] = ec1->beerBias[b];

  for (int b = 0; b < ec->nBeers; b ++)
    for (int e = 0; e < ec->E; e ++)
      for (int k = 0; k < ec->K; k ++)
        ec->beerLatent[b][e][k] = ec1->beerLatent[b][0][k];
  for (int u = 0; u < ec->nUsers; u ++)
    for (int e = 0; e < ec->E; e ++)
      for (int k = 0; k < ec->K; k ++)
        ec->userLatent[u][e][k] = ec1->userLatent[u][0][k];
}

void experiment(char* c, int mode, int evaluation, int E, int K)
{
  // All hyperparameters set to 1.
  int lambda1 = 1;
  int lambda2 = 1;
  corpus corp(c, 0);
  
  // First train a standard recommender system
  expCorpus ec1(&corp, 1, 10, lambda1, 0, RECOMMENDER, evaluation);
  printf("Training latent-factor recommender system...\n");
  ec1.train(1, 100);

  if (mode != RECOMMENDER)
  {
    printf("Training experience-based recommender system...\n");
    // Next, copy its parameters for each experience level to initialize the experience-based model
    expCorpus ec(&corp, E, K, lambda1, lambda2, mode, evaluation);
    copyParameters(&ec1, &ec);
    
    // Train the experience based model
    ec.train(10, 25);
  }
}

int main(int argc, char** argv)
{
  if (argc != 2)
  {
    printf("Please specify an input file\n");
    exit(0);
  }

  //int mode = LEARNED_USER_EVOLUTION; // Mode (lf/a/b/c/d from the WWW paper, see common.hpp)
  int mode = LEARNED_USER_EVOLUTION; // Mode (lf/a/b/c/d from the WWW paper, see common.hpp)
  int testMode = FINALVOTE; // Testing setting (Table 2/3 from the WWW paper, see common.hpp)

  experiment(argv[1], mode, testMode, 5, 5);
}
