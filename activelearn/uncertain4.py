#!/usr/bin/env python
# encode: utf-8

# Active Learning (Uncertainly Sampling and Information Density) for 20 newsgroups
# This code is available under the MIT License.
# (c)2013 Nakatani Shuyo / Cybozu Labs Inc.

import optparse
import numpy
import sklearn.datasets
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

def activelearn(results, data, test, strategy, train, pool, classifier_factory, max_train, densities):
    print strategy

    # copy initial indexes of training and pool
    train = list(train)
    pool = list(pool)

    accuracies = []
    while len(train) < max_train:
        if len(accuracies) > 0:
            if strategy == "random":
                x = numpy.random.randint(len(pool))
            else:
                predict = cl.predict_proba(data.data[pool,:])
                if strategy == "least confident":
                    x = predict.max(axis=1)
                elif strategy == "margin sampling":
                    predict.sort(axis=1)
                    x = (predict[:,-1] - predict[:,-2])
                elif strategy == "entropy-based":
                    x = numpy.nan_to_num(predict * numpy.log(predict)).sum(axis=1)
                if densities != None: x *= densities[pool]
                x = x.argmin()
            train.append(pool[x])
            del pool[x]

        cl = classifier_factory()
        cl.fit(data.data[train,:], data.target[train])
        accuracy = cl.score(test.data, test.target)
        print "%s %d : %f" % (strategy, len(train), accuracy)
        accuracies.append(accuracy)

    results.append((strategy, accuracies))


def main():
    parser = optparse.OptionParser()
    parser.add_option("-r", dest="method_random", action="store_true", help="use random sampling", default=False)
    parser.add_option("-l", dest="method_least", action="store_true", help="use least confident", default=False)
    parser.add_option("-m", dest="method_margin", action="store_true", help="use margin sampling", default=False)
    parser.add_option("-e", dest="method_entropy", action="store_true", help="use entropy-based method", default=False)
    parser.add_option("-a", dest="method_all", action="store_true", help="use all methods", default=False)

    parser.add_option("--nb", dest="naive_bayes", type="float", help="use naive bayes classifier", default=None)
    parser.add_option("--lr1", dest="logistic_l1", type="float", help="use logistic regression with l1-regularity", default=None)
    parser.add_option("--lr2", dest="logistic_l2", type="float", help="use logistic regression with l2-regularity", default=None)

    parser.add_option("-n", dest="max_train", type="int", help="max size of training", default=300)
    parser.add_option("-t", dest="training", help="specify indexes of training", default=None)

    parser.add_option("-b", dest="beta", type="float", help="density importance", default=0)

    parser.add_option("--seed", dest="seed", type="int", help="random seed")
    (opt, args) = parser.parse_args()
    numpy.random.seed(opt.seed)

    data = sklearn.datasets.fetch_20newsgroups_vectorized()
    print "(train size, voca size) : (%d, %d)" % data.data.shape

    N_CLASS = data.target.max() + 1
    if opt.training:
        train = [int(x) for x in opt.training.split(",")]
    else:
        train = [numpy.random.choice((data.target==k).nonzero()[0]) for k in xrange(N_CLASS)]
    print "indexes of training set : ", ",".join("%d" % x for x in train)

    pool = range(data.data.shape[0])
    for x in train: pool.remove(x)

    methods = []
    if opt.method_all:
        methods = ["random", "least confident", "margin sampling", "entropy-based"]
    else:
        if opt.method_random: methods.append("random")
        if opt.method_least: methods.append("least confident")
        if opt.method_margin: methods.append("margin sampling")
        if opt.method_entropy: methods.append("entropy-based")

    if len(methods) > 0:
        test = sklearn.datasets.fetch_20newsgroups_vectorized(subset='test')
        print "(test size, voca size) : (%d, %d)" % test.data.shape

        densities = None
        if opt.beta > 0:
            densities = ((data.data * data.data.T).sum(axis=0).A[0] - 1) ** opt.beta

        if opt.logistic_l1:
            print "Logistic Regression with L1-regularity : C = %f" % opt.logistic_l1
            classifier_factory = lambda: LogisticRegression(penalty='l1', C=opt.logistic_l1)
        elif opt.logistic_l2:
            print "Logistic Regression with L2-regularity : C = %f" % opt.logistic_l2
            classifier_factory = lambda: LogisticRegression(C=opt.logistic_l2)
        else:
            a = opt.naive_bayes or 0.01
            print "Naive Bayes Classifier : alpha = %f" % a
            classifier_factory = lambda: MultinomialNB(alpha=a)

        results = []
        for x in methods:
            activelearn(results, data, test, x, train, pool, classifier_factory, opt.max_train, densities)

        print "\t%s" % "\t".join(x[0] for x in results)
        d = len(train)
        for i in xrange(len(results[0][1])):
            print "%d\t%s" % (i+d, "\t".join("%f" % x[1][i] for x in results))


if __name__ == "__main__":
    main()
