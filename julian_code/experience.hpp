#include "common.hpp"

class expCorpus
{
public:
  expCorpus(corpus* corp, // Corpus of ratings
            int E, // Number of distinct experience levels
            int K, // Number of latent factors
            double lambda1, // prior on parameters (gamma)
            double lambda2, // smoothness prior
            int trainMode,
            int testMode) :
    corp(corp), E(E), K(K), lambda1(lambda1), lambda2(lambda2), trainMode(trainMode), testMode(testMode)
  {
    srand(0);

    int nValid = 1; // Number of ratings (per user) to use for validation
    int nTest = 1; // Number of ratings (per user) to use for testing
    
    nUsers = corp->nUsers;
    nBeers = corp->nBeers;
    
    votesPerUser = new std::vector<vote*> [nUsers]; // Maps a user to a vector of their ratings
    votesPerBeer = new std::vector<vote*> [nBeers]; // Maps an item to a vectors of its ratings

    validVotesPerUser = new std::vector<vote*> [nUsers]; // Validation ratings for each user
    testVotesPerUser = new std::vector<vote*> [nUsers]; // Test ratings for each user
    
    long oldestInCorpus = std::numeric_limits<long>::max();
    long newestInCorpus = 0;

    for (std::vector<vote*>::iterator it = corp->V->begin(); it != corp->V->end(); it ++)
    {
      vote* vi = *it;
      votesPerUser[vi->user].push_back(vi);
    }

    for (int user = 0; user < nUsers; user ++)
    {
      sort(votesPerUser[user].begin(), votesPerUser[user].end(), voteCompare);
      long y2k = 946684800;
      if (votesPerUser[user].front()->voteTime < oldestInCorpus and votesPerUser[user].front()->voteTime > y2k) oldestInCorpus = votesPerUser[user].front()->voteTime;
      if (votesPerUser[user].back()->voteTime > newestInCorpus) newestInCorpus = votesPerUser[user].back()->voteTime;

      // Divide the ratings into training/validation/test sets
      if (testMode == FINALVOTE)
      {
        for (int i = 0; i < nValid; i ++)
        {
          if (votesPerUser[user].size() <= 1) break;
          validVotesPerUser[user].push_back(votesPerUser[user].back());
          votesPerUser[user].pop_back();
        }
        for (int i = 0; i < nTest; i ++)
        {
          if (votesPerUser[user].size() <= 1) break;
          testVotesPerUser[user].push_back(votesPerUser[user].back());
          votesPerUser[user].pop_back();
        }
        for (std::vector<vote*>::iterator it = validVotesPerUser[user].begin(); it != validVotesPerUser[user].end(); it ++)
          nearestVote[*it] = votesPerUser[user].back();
        for (std::vector<vote*>::iterator it = testVotesPerUser[user].begin(); it != testVotesPerUser[user].end(); it ++)
          nearestVote[*it] = votesPerUser[user].back();
      }
      else if (testMode == RANDOMVOTE)
      {
        std::vector<int> options;
        for (int i = 0; i < (int) votesPerUser[user].size(); i ++)
          options.push_back(i);
        random_shuffle(options.begin(), options.end());
        std::set<int> banned;
        std::vector<int> toDelete;
        banned.insert(0);
        int ind = 0;
        while (ind < (int) options.size() and (int) toDelete.size() < nValid + nTest)
        {
          if (banned.find(options[ind]) == banned.end())
          {
            vote* vi = votesPerUser[user][options[ind]];
            vote* pvi = votesPerUser[user][options[ind] - 1];
            nearestVote[vi] = pvi;
            banned.insert(options[ind] + 1);
            banned.insert(options[ind] - 1);
            toDelete.push_back(options[ind]);
          }
          ind ++;
        }
        if ((int) toDelete.size() == nValid + nTest)
        {
          for (int i = 0; i < nValid; i ++)
            validVotesPerUser[user].push_back(votesPerUser[user][toDelete[i]]);
          for (int i = nValid; i < nValid + nTest; i ++)
            testVotesPerUser[user].push_back(votesPerUser[user][toDelete[i]]);
          sort(toDelete.begin(), toDelete.end());
          reverse(toDelete.begin(), toDelete.end());
          for (std::vector<int>::iterator it = toDelete.begin(); it != toDelete.end(); it ++)
            votesPerUser[user].erase(votesPerUser[user].begin() + *it);
        }
      }

      // Initialize the experience variables
      for (int i = 0; i < (int) votesPerUser[user].size(); i ++)
      {
        vote* vi = votesPerUser[user][i];
        
        if (trainMode == STATIC_USER_EVOLUTION or trainMode == LEARNED_USER_EVOLUTION)
        { // statically increasing experience level per user
          float f = i * 1.0/votesPerUser[user].size() * E;
          userExperience[vi] = int(f); // Just initialize using an increasing experience level.
        }
        else if (trainMode == STATIC_COMMUNITY_EVOLUTION or trainMode == LEARNED_COMMUNITY_EVOLUTION)
        { // statically increasing experience level per item
          double posInSeq = (vi->voteTime - oldestInCorpus) * 1.0 / (1.0 + newestInCorpus - oldestInCorpus);
          int f = int(posInSeq * E);
          if (f < 0) f = 0;
          if (f >= E) f = E - 1;
          userExperience[vi] = int(f);
        }
        else // trainMode == RECOMMENDER
          userExperience[vi] = 0;
      }
    }

    for (int user = 0; user < nUsers; user ++)
      for (std::vector<vote*>::iterator it = votesPerUser[user].begin(); it != votesPerUser[user].end(); it ++)
      {
        vote* vi = *it;
        trainVotes.push_back(vi);
        votesPerBeer[vi->item].push_back(vi);
      }

    // Sort ratings by time
    sort(trainVotes.begin(), trainVotes.end(), voteCompare);

    for (int beer = 0; beer < nBeers; beer ++)
      sort(votesPerBeer[beer].begin(), votesPerBeer[beer].end(), voteCompare);

    NW = 1 + // alpha
         E + // effectE
         nBeers*E + // beta_item (for each
         nUsers*E + // beta_user
         (nBeers + nUsers)*E*K + 
         nBeers + nUsers; // offsets

    double* x = new double [NW];
    for (int i = 0; i < NW; i ++)
      x[i] = 0;

    getG(x, &alpha, &effectE, &beerD, &userD, &beerBias, &userBias, &beerLatent, &userLatent, true);

    // Set alpha to the average rating
    for (std::vector<vote*>::iterator it = trainVotes.begin(); it != trainVotes.end(); it ++)
    {
      vote* vi = *it;
      alpha += vi->value;
    }
    alpha /= trainVotes.size();

    // Randomly initialize all other parameters
    for (int b = 0; b < nBeers; b ++)
      for (int e = 0; e < E; e ++)
        for (int k = 0; k < K; k ++)
          beerLatent[b][e][k] = rand() / (1.0*RAND_MAX);

    for (int u = 0; u < nUsers; u ++)
      for (int e = 0; e < E; e ++)
        for (int k = 0; k < K; k ++)
          userLatent[u][e][k] = rand() / (1.0*RAND_MAX);

    delete [] x;
  }

  ~expCorpus()
  {
    delete [] votesPerBeer;
    delete [] votesPerUser;
    delete [] validVotesPerUser;
    delete [] testVotesPerUser;

    clearG(&alpha, &effectE, &beerD, &userD, &beerBias, &userBias, &beerLatent, &userLatent);
  }

  double prediction(int experience, vote* vi);
  double testError(bool validate, FILE* outFile);
  int predictExpLevel();
  int predictExpLevelForCommunity();
  void dl(double* grad);
  double lsq(bool addreg);
  void train(int emIterations, int gradIterations);

  corpus* corp;
  std::vector<vote*> trainVotes;

  // Ratings for each product, sorted by timestamp.
  std::vector<vote*>* votesPerBeer;
  std::vector<vote*>* votesPerUser;
  
  std::vector<vote*>* validVotesPerUser;
  std::vector<vote*>* testVotesPerUser;

  // Latent variables
  std::map<vote*, int> userExperience;
  
  std::map<vote*, vote*> nearestVote;

  int putG(double* g, double alpha, double* effectE, double** beerD, double** userD, double* beerBias, double* userBias, double*** beerLatent, double*** userLatent);
  int getG(double* g, double* alpha, double** effectE, double*** beerD, double*** userD, double** beerBias, double** userBias, double**** beerLatent, double**** userLatent, bool init);
  void clearG(double* alpha, double** effectE, double*** beerD, double*** userD, double** beerBias, double** userBias, double**** beerLatent, double**** userLatent);

  // Model parameters
  double alpha; // Offset term (alpha)
  double* effectE; // Change in offset term per experience level
  
  double* beerBias; // Item bias term (beta_item)
  double* userBias; // User bias term (beta_user)
  double** beerD; // Change in (item) bias term per experience level
  double** userD; // Change in (user) bias term per experience level

  double*** beerLatent; // Item latent term (gamma_item) per experience level
  double*** userLatent; // User latent term (gamma_item) per experience level
  
  int NW; // Total number of parameters

  int E; // Number of experience levels
  int K; // Number of latent factors
  
  int nUsers; // Number of users
  int nBeers; // Number of items

  // Hyperparameters
  double lambda1; // Regularizer on parameters
  double lambda2; // Smoothness between successive experience levels

  int trainMode; // Training setting (see common.hpp)
  int testMode; // Testing setting (see common.hpp)
};
