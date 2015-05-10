#!/usr/bin/env python

from numpy import asarray, random, sqrt, sum, zeros
from scipy.spatial import distance
from scipy.stats import rankdata

def Test(X, Y, perms=10000, method='pearson'):
  """
  Takes two distance matrices (either redundant matrices or condensed
  vectors) and performs a Mantel test. The Mantel test is a significance
  test of the correlation between two distance matrices.

  Parameters
  ----------
  X : array_like
      First distance matrix (condensed or redundant).
  Y : array_like
      Second distance matrix (condensed or redundant), where the order
      of elements corresponds to the order of elements in the first matrix.
  perms : int, optional
      The number of permutations to perform (default: 10000). A larger
      number gives a more reliable Z-score but takes longer to run.
  method : str, optional
      Type of correlation coefficient to use; either 'pearson' or 
      'spearman' (default: 'pearson').

  Returns
  -------
  z : float
      A standard score (z-score)
  r : float
      Veridical correlation
  m : float
      Mean of Monte Carlo sample correlations
  sd : float
      Standard deviation of Monte Carlo sample correlations
  """

  # Ensure X and Y are arrays.

  X = asarray(X, dtype=float)
  Y = asarray(Y, dtype=float)

  # Check that X and Y are valid distance matrices/vectors.

  if distance.is_valid_dm(X) == False and distance.is_valid_y(X) == False:
    raise ValueError('X is not a valid distance matrix')

  if distance.is_valid_dm(Y) == False and distance.is_valid_y(Y) == False:
    raise ValueError('Y is not a valid distance matrix')

  # If X or Y is a matrix, condense it to a vector.

  if len(X.shape) == 2:
    X = distance.squareform(X, 'tovector', False)

  if len(Y.shape) == 2:
    Y = distance.squareform(Y, 'tovector', False)

  # Check for size equality.

  if X.shape[0] != Y.shape[0]:
    raise ValueError('X and Y are not of equal size')

  # If Spearman correlation is requested, convert X and Y to ranks.

  if method == 'spearman':
    X = rankdata(X)
    Y = rankdata(Y)

  # Compute parts of the correlation coefficient that can be done outside the Monte Carlo loop.

  X_res = X - X.mean() # X residuals
  Y_res = Y - Y.mean() # Y residuals
  X_ss = sum(X_res * X_res) # X sum-of-squares
  Y_ss = sum(Y_res * Y_res) # Y sum-of-squares
  denominator = sqrt(X_ss * Y_ss) # Denominator of the correlation coefficient

  # Reformat Y_res as a distance matrix and determine its size.

  Y_res_as_matrix = distance.squareform(Y_res, 'tomatrix', False) # Y_res in matrix form
  n = Y_res_as_matrix.shape[0] # Matrix size (N x N)

  # Initialize some empty arrays.

  Y_res_permuted = zeros(Y_res.shape[0], dtype=float) # Empty array to store permutations of Y_res
  MC_corrs = zeros(perms, dtype=float) # Empty array to store Monte Carlo sample correlations

  # Monte Carlo loop.

  for i in xrange(perms):
    order = random.permutation(n) # Random order in which to permute the matrix    
    Y_res_as_matrix_permuted = Y_res_as_matrix[order, :][:, order] # Permute the matrix
    distance._distance_wrap.to_vector_from_squareform_wrap(Y_res_as_matrix_permuted, Y_res_permuted) # Convert back to vector
    MC_corrs[i] = sum(X_res * Y_res_permuted) / denominator # Store the correlation between X and a permuation of Y

  # Calculate and return the stats.

  r = sum(X_res * Y_res) / denominator # Veridical correlation
  m = MC_corrs.mean() # Mean of Monte Carlo sample correlations
  sd = MC_corrs.std() # Standard deviation of Monte Carlo sample correlations
  z = (r - m) / sd # Z-score

  return z, r, m, sd