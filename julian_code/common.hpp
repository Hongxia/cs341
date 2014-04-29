#pragma once

#include "stdio.h"
#include "stdlib.h"
#include "vector"
#include "math.h"
#include "string.h"
#include <string>
#include <iostream>
#include "omp.h"
#include "map"
#include "set"
#include "vector"
#include "common.hpp"
#include "algorithm"
#include "lbfgs.h"

enum
{
  RECOMMENDER, // A "standard" latent-factor recommender system that ignores temporal information (lf)
  STATIC_COMMUNITY_EVOLUTION, // Community evolves at uniform rate (a)
  STATIC_USER_EVOLUTION, // Users evolve at a uniform rate (b)
  LEARNED_COMMUNITY_EVOLUTION, // Community evolves at a learned rate (c)
  LEARNED_USER_EVOLUTION // Users evolve at a learned rate (d)
};

enum
{
  FINALVOTE, // Users' most recent reviews
  RANDOMVOTE // Random subset of users' reviews
};

struct vote
{
  // stuff used by recommender system
  int user;
  int item;
  float value; // rating

  // additional stuff for experience system
  long voteTime; // unix time
};

typedef struct vote vote;

/// Used to sort ratings by time
bool voteCompare(vote* i, vote* j)
{
  return (i->voteTime < j->voteTime);
}

template <typename T> int sgn(T val)
{
  return (val > T(0)) - (val < T(0));
}

/// Class to read a corpus of ratings
class corpus
{
public:
  corpus(std::string voteFile, int max)
  {
    nUsers = 0;
    nBeers = 0;
    FILE* f = fopen(voteFile.c_str(), "r");
    V = new std::vector<vote*>();
    vote* v = new vote();
    std::map<std::string, int> userIds;
    std::map<std::string, int> beerIds;

    char* uName = new char [100];
    char* bName = new char [100];
    int ind = 0;
    // Files should be lines containing quadruples of (user, item, rating, time)
    while (fscanf(f, "%s %s %f %ld", uName, bName, &(v->value), &(v->voteTime)) == 4)
    {
      std::string uS(uName);
      std::string bS(bName);
      if (userIds.find(uS) == userIds.end())
      {
        rUserIds[nUsers] = uS;
        userIds[uS] = nUsers ++;
      }
      if (beerIds.find(bS) == beerIds.end())
      {
        rBeerIds[nBeers] = bS;
        beerIds[bS] = nBeers ++;
      }
      v->user = userIds[uS];
      v->item = beerIds[bS];

      V->push_back(v);
      v = new vote();
      if (max > 0 and ind + 1 >= max) break;
      ind ++;
    }
    
    sort(V->begin(), V->end(), voteCompare);
    
    delete v;
    delete [] uName;
    delete [] bName;

    fclose(f);
  }
  
  ~corpus()
  {
    for (std::vector<vote*>::iterator it = V->begin(); it != V->end(); it ++)
      delete *it;
    delete V;
  }

  std::vector<vote*>* V;
  
  int nUsers;
  int nBeers;
  
  std::map<std::string, int> userIds; // Maps user IDs (strings) to integer IDs
  std::map<std::string, int> beerIds; // Maps product IDs to integer IDs
  
  std::map<int, std::string> rUserIds; // Inverse of the above map
  std::map<int, std::string> rBeerIds;
};
