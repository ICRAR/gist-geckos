#######################################################################
# ;
# ; Copyright (C) 1999-2016, Michele Cappellari
# ; E-mail: michele.cappellari_at_physics.ox.ac.uk
# ;
# ; Updated versions of the software are available from my web page
# ; http://purl.org/cappellari/software
# ;
# ; If you have found this software useful for your research,
# ; I would appreciate an acknowledgment and a link to the website.
# ;
# ; This software is provided as is without any warranty whatsoever.
# ; Permission to use, for non-commercial purposes is granted.
# ; Permission to modify for personal or internal use is granted,
# ; provided this copyright and disclaimer are included unchanged
# ; at the beginning of the file. All other rights are reserved.
# ;
# ;######################################################################
# ;+
# ; NAME:
# ;   BVLS
# ;
# ; AUTHOR:
# ;   Michele Cappellari, Leiden Observatory, The Netherlands
# ;   Currently at the University of Oxford UK (michele.cappellari_at_physics.ox.ac.uk)
# ;
# ; PURPOSE:
# ;   Perform bound constrained linear least-squares minimization
# ;
# ; CATEGORY:
# ;   Least Squares
# ;
# ; CALLING SEQUENCE:
# ;   BVLS, A, B, BND, X, $
# ;       EPS=eps, /FASTNORM, IERR=ierr, INDEX=index, ITER=iter, $
# ;       ITMAX=itmax, NSETP=nsetp, RNORM=rnorm, W=w
# ;
# ; DESCRIPTION:
# ;
# ;   Given an M by N matrix, A(M,N), and an M-vector, B(M),  compute an
# ;   N-vector, X(N), that solves the least-squares problem A # X = B
# ;   (in IDL notation) subject to X(J) satisfying
# ;   BND(0,J) <= X(J) <= BND(1,J)
# ;
# ;   The values BND(0,J) = -(MACHAR()).XMAX and BND(1,J) = (MACHAR()).XMAX
# ;   are suggested choices to designate that there is no constraint in that
# ;   direction.
# ;
# ;   This algorithm is a generalization of  NNLS, that solves
# ;   the least-squares problem,  A # X = B,  subject to all X(J) >= 0.
# ;   The subroutine NNLS appeared in 'SOLVING LEAST SQUARES PROBLEMS,'
# ;   by Lawson and Hanson, Prentice-Hall, 1974.  Work on BVLS was started
# ;   by C. L. Lawson and R. J. Hanson at Jet Propulsion Laboratory,
# ;   1973 June 12.  Many modifications were subsequently made.
# ;   The Fortran 90 code was completed in April, 1995 by R. J. Hanson.
# ;   The BVLS package is an additional item for the reprinting of the book
# ;   by SIAM Publications and the distribution of the code package
# ;   using netlib and Internet or network facilities.
# ;
# ;   This IDL version was ported from the original Fortran 90 code
# ;   by Michele Cappellari, Leiden Observatory, The Netherlands
# ;
# ; INPUT PARAMETERS:
# ;
# ;   A(M,N)     [INTENT(InOut)]
# ;       On entry A() contains the M by N matrix, A.
# ;       On return A() contains the product matrix, Q*A, where
# ;       Q is an M by M orthogonal matrix generated by this
# ;       subroutine.  The dimensions are M=size(A,1) and N=size(A,2).
# ;
# ;   B(M)     [INTENT(InOut)]
# ;       On entry B() contains the M-vector, B.
# ;       On return, B() contains Q*B.  The same Q multiplies A.
# ;
# ;   BND(2,N)  [INTENT(In)]
# ;       BND(0,J) is the lower bound for X(J).
# ;       BND(1,J) is the upper bound for X(J).
# ;       Require:  BND(0,J) <= BND(1,J).
# ;
# ; OUTPUT PARAMETER:
# ;
# ;   X(N)    [INTENT(Out)]
# ;       On entry X() need not be initialized.  On return,
# ;       X() will contain the solution N-vector.
# ;
# ; KEYWORD PARAMETERS:
# ;
# ;   RNORM    [INTENT(Out)]
# ;       The Euclidean norm of the residual vector, b - A*X.
# ;
# ;   NSETP    [INTENT(Out)]
# ;       Indicates the number of components of the solution
# ;       vector, X(), that are not at their constraint values.
# ;
# ;   W(N)     [INTENT(Out)]
# ;       An N-array.  On return, W() will contain the dual solution
# ;       vector.   Using Set definitions below:
# ;       W(J) = 0 for all j in Set P,
# ;       W(J) <= 0 for all j in Set Z, such that X(J) is at its
# ;       lower bound, and
# ;       W(J) >= 0 for all j in Set Z, such that X(J) is at its
# ;       upper bound.
# ;       If BND(1,J) = BND(2,J), so the variable X(J) is fixed,
# ;       then W(J) will have an arbitrary value.
# ;
# ;   INDEX(N)    [INTENT(Out)]
# ;       An INTEGER working array of size N.  On exit the contents
# ;       of this array define the sets P, Z, and F as follows:
# ;
# ;   INDEX(1)   through INDEX(NSETP) = Set P.
# ;   INDEX(IZ1) through INDEX(IZ2)   = Set Z.
# ;   INDEX(IZ2+1) through INDEX(N)   = Set F.
# ;   IZ1 = NSETP + 1 = NPP1
# ;       Any of these sets may be empty.  Set F is those components
# ;       that are constrained to a unique value by the given
# ;       constraints.   Sets P and Z are those that are allowed a non-
# ;       zero range of values.  Of these, set Z are those whose final
# ;       value is a constraint value, while set P are those whose
# ;       final value is not a constraint.  The value of IZ2 is not returned.
# ;...    It is computable as the number of bounds constraining a component
# ;...    of X uniquely.
# ;
# ;   IERR    [INTENT(Out)]
# ;   Indicates status on return.
# ;   = 0   Solution completed.
# ;       = 1   M <= 0 or N <= 0
# ;       = 2   B(:), X(:), BND(:,:), W(:), or INDEX(:) size or shape violation.
# ;       = 3   Input bounds are inconsistent.
# ;       = 4   Exceed maximum number of iterations.
# ;
# ;   EPS [real(kind(one))]
# ;       Determines the relative linear dependence of a column vector
# ;       for a variable moved from its initial value.  This is used in
# ;       one place with the default value EPS=(MACHAR()).EPS.  Other
# ;       values, larger or smaller may be needed for some problems.
# ;
# ;   ITMAX  [integer]
# ;       Set to 3*N.  Maximum number of iterations permitted.
# ;       This is usually larger than required.
# ;
# ;   ITER   [integer]
# ;       Iteration counter.
# ;
# ;   /FASTNORM
# ;       Perform Euclidean Norm computation without checking for over/underflows.
# ;       It can speed up the program considerably when M is large, but has to
# ;       be used with care since may lead to instabilities!
# ;
# ; MODIFICATION HISTORY:
# ;   V1.0: Written by Michele Cappellari, Padova, 2000
# ;   V1.1: Added /FASTNORM keyword, MC, Leiden, 20 September 2001
# ;   V1.2: Use MAKE_ARRAY to deal with float or double arrays,
# ;       MC, Leiden, 19 October 2001
# ;   V1.3: Added compilation options and converted to IDL V5.0,
# ;       MC, Leiden 20 May 2002
# ;   V1.4: Define optional parameters using optional keywords.
# ;       The new calling sequence is not directly compatible with
# ;       the previous versions. MC, Leiden, 20 March 2004
# ;   V1.41: Minor updates to the documentation. MC, Oxford, 01 March 2010
# ;   V1.42: Updated to IDL 6 Compound Assignment Operators.
# ;       MC, Oxford, 2 August 2016
# ;-
# ;----------------------------------------------------------------------

# from astropy.io import fits
import sys

# import pdb
# import math as mt
import numpy as np
# import glob
# import copy
# import astropy.convolution as ap_c
# import scipy.special as sp_s
# import scipy.optimize as sp_op
# from cap_mpfit import mpfit
# import ppxf
# from ppxf import _bvls_solve, robust_sigma
# import matplotlib.pyplot as plt
# import matplotlib.colors as colors
# from matplotlib.font_manager import FontProperties
# import dill
# import ppxf_util as util
# from scipy import misc, fftpack
# from numpy.polynomial import legendre, hermite
from goto import with_goto

# import pprint

# np.set_printoptions(suppress=True)
# np.set_printoptions(threshold=20)
# np.set_printoptions(threshold=400)

# _____________________________ GLOBALS _______________________________

global FIND  # = []
global HITBND  # = []
global FREE1  # = []
global FREE2  # = []
global FREE  # = []
global IERR  # = []
global M  # = []
global N  # = []
global I  # = []
global IBOUND  # = []
global II  # = []
global IP  # = []
global ITER  # = []
global ITMAX  # = []
global IZ  # = []
global IZ1  # = []
global IZ2  # = []
global J  # = []
global JJ  # = []
global JZ  # = []
global L  # = []
global LBOUND  # = []
global NPP1  # = []
global NSETP  # = []
global INDEX  # = []
global ZERO  # = []
global ONE  # = []
global TWO  # = []
global A  # = []
global B  # = []
global S  # = []
global X  # = []
global W  # = []
global Z  # = []
global BND  # = []
global ALPHA  # = []
global ASAVE  # = []
global CC  # = []
global EPS  # = []
global RANGE  # = []
global RNORM  # = []
global NORM  # = []
global SM  # = []
global SS  # = []
global T  # = []
global UNORM  # = []
global UP  # = []
global ZTEST  # = []
global FASTNORM  # = []


# ; --------------------------------------------------------------------
@with_goto
def NRM2(X2, fastNorm):
    # ;
    # ;   NRM2 returns the Euclidean norm of a vector so that
    # ;
    # ;   NRM2 := sqrt( x'*x )
    # ;

    if fastNorm == 1:
        return np.sqrt(
            np.sum(np.power(X2, 2, dtype=np.float32)), dtype=np.float32
        )  # brute force approach: use with care!
    ZERO1 = np.float32(0.0)
    ONE1 = np.float32(1.0)
    N2 = len(X2)

    if N2 < 1:
        NORM1 = np.float32(ZERO1)
    else:
        if N2 == 1:
            NORM1 = np.absolute(X2[0], dtype=np.float32)
        else:
            SCALE1 = np.float32(ZERO1)
            SSQ1 = np.float32(ONE1)
            for IX in xrange(0, N2):
                ABSXI1 = np.absolute(X2[IX], dtype=np.float32)
                if ABSXI1 > ZERO1:
                    if SCALE1 < ABSXI1:
                        DD1 = np.divide(SCALE1, ABSXI1, dtype=np.float32)
                        PP1 = np.power(DD1, 2, dtype=np.float32)
                        TT1 = np.multiply(SSQ1, PP1, dtype=np.float32)
                        SSQ1 = np.add(np.float32(ONE1), TT1, dtype=np.float32)
                        SCALE1 = np.float32(ABSXI1)
                    else:
                        DD1 = np.divide(ABSXI1, SCALE1, dtype=np.float32)
                        SSQ1 = np.add(
                            SSQ1, np.power(DD1, 2, dtype=np.float32), dtype=np.float32
                        )

            NORM1 = np.multiply(
                np.float32(SCALE1), np.sqrt(SSQ1, dtype=np.float32), dtype=np.float32
            )
    return np.float32(NORM1)


# ;----------------------------------------------------------------------
@with_goto
def TERMINATION():
    #  global FIND, HITBND, FREE1, FREE2, FREE, IERR, M, N, I, IBOUND, II, IP, ITER, ITMAX,
    #  IZ, IZ1, IZ2, J, JJ, JZ, L, LBOUND, NPP1, NSETP, INDEX, ZERO, ONE, TWO, A, B, S, X,
    #  W, Z, BND, ALPHA, ASAVE, CC, EPS, RANGE, RNORM, NORM, SM, SS, T, UNORM, UP, ZTEST, FASTNORM

    global FIND
    global HITBND
    global FREE1
    global FREE2
    global FREE
    global IERR
    global M
    global N
    global I
    global IBOUND
    global II
    global IP
    global ITER
    global ITMAX
    global IZ
    global IZ1
    global IZ2
    global J
    global JJ
    global JZ
    global L
    global LBOUND
    global NPP1
    global NSETP
    global INDEX
    global ZERO
    global ONE
    global TWO
    global A
    global B
    global S
    global X
    global W
    global Z
    global BND
    global ALPHA
    global ASAVE
    global CC
    global EPS
    global RANGE
    global RNORM
    global NORM
    global SM
    global SS
    global T
    global UNORM
    global UP
    global ZTEST
    global FASTNORM

    #
    #    IF (IERR LE 0) THEN BEGIN
    # ;
    # ;   Compute the norm of the residual vector.

    SM = np.copy(ZERO)
    if NPP1 <= M:
        SM = NRM2(B[NPP1 - 1 : M], FASTNORM)
    else:
        W[0:N] = np.float32(ZERO)
    RNORM = np.copy(SM)
    return


# END ; ( TERMINATION )


# ;----------------------------------------------------------------------
@with_goto
def MOVE_COEF_I_FROM_SET_P_TO_SET_Z():
    global FIND
    global HITBND
    global FREE1
    global FREE2
    global FREE
    global IERR
    global M
    global N
    global I
    global IBOUND
    global II
    global IP
    global ITER
    global ITMAX
    global IZ
    global IZ1
    global IZ2
    global J
    global JJ
    global JZ
    global L
    global LBOUND
    global NPP1
    global NSETP
    global INDEX
    global ZERO
    global ONE
    global TWO
    global A
    global B
    global S
    global X
    global W
    global Z
    global BND
    global ALPHA
    global ASAVE
    global CC
    global EPS
    global RANGE
    global RNORM
    global NORM
    global SM
    global SS
    global T
    global UNORM
    global UP
    global ZTEST
    global FASTNORM

    X[I - 1] = np.copy(BND[IBOUND - 1, I - 1])
    if (np.absolute(X[I - 1], dtype=np.float32) > ZERO) and (JJ > 0):
        B[0:JJ] = np.subtract(
            B[0:JJ],
            np.multiply(A[0:JJ, I - 1], X[I - 1], dtype=np.float32),
            dtype=np.float32,
        )

    # ;   The following loop can be null.

    for J in np.arange(JJ + 1, NSETP + 1):
        II = np.copy(INDEX[J - 1])
        INDEX[J - 2] = np.copy(II)
        SCALE = np.sum(
            np.absolute(A[J - 2 : J, II - 1], dtype=np.float32), dtype=np.float32
        )
        if SCALE > ZERO:
            DD1 = np.divide(A[J - 2 : J, II - 1], np.float32(SCALE), dtype=np.float32)
            PP1 = np.power(DD1, 2, dtype=np.float32)
            TT1 = np.sum(PP1, dtype=np.float32)
            R = np.multiply(SCALE, np.sqrt(TT1, dtype=np.float32), dtype=np.float32)
            if np.absolute(A[J - 2, II - 1], dtype=np.float32) > np.absolute(
                A[J - 1, II - 1], dtype=np.float32
            ):
                ROE = A[J - 2, II - 1]
            else:
                ROE = A[J - 1, II - 1]
            if ROE < ZERO:
                R = np.negative(R, dtype=np.float32)
            CC = np.divide(A[J - 2, II - 1], R, dtype=np.float32)
            SS = np.divide(A[J - 1, II - 1], R, dtype=np.float32)
            A[J - 2, II - 1] = R
        else:
            CC = np.float32(ONE)
            SS = np.float32(ZERO)
        SM = A[J - 2, II - 1]

        # ;
        # ;   The plane rotation is applied to two rows of A and the right-hand
        # ;   side.  One row is moved to the scratch array S and THEN the updates
        # ;   are computed.  The intent is for array operations to be performed
        # ;   and minimal extra data movement.  One extra rotation is applied
        # ;   to column II in this approach.

        S = np.copy(A[J - 2, 0:N])
        A[J - 2, 0:N] = np.multiply(CC, S, dtype=np.float32) + np.multiply(
            SS, A[J - 1, 0:N], dtype=np.float32
        )
        A[J - 1, 0:N] = np.subtract(
            np.multiply(CC, A[J - 1, 0:N], dtype=np.float32),
            np.multiply(SS, S, dtype=np.float32),
            dtype=np.float32,
        )
        A[J - 2, II - 1] = np.copy(SM)
        A[J - 1, II - 1] = np.copy(ZERO)
        SM = np.copy(B[J - 2])
        B[J - 2] = np.multiply(CC, SM, dtype=np.float32) + np.multiply(
            SS, B[J - 1], dtype=np.float32
        )
        B[J - 1] = np.subtract(
            np.multiply(CC, B[J - 1], dtype=np.float32),
            np.multiply(SS, SM, dtype=np.float32),
            dtype=np.float32,
        )
    # ENDFOR
    J = J + 1  # Account for the change as in IDL
    NPP1 = np.copy(NSETP)
    NSETP = NSETP - 1
    IZ1 = IZ1 - 1
    INDEX[IZ1 - 1] = np.copy(I)

    return


# END ; ( MOVE COEF I FROM SET P TO SET Z )


# ;----------------------------------------------------------------------
@with_goto
def SEE_IF_ALL_CONSTRAINED_COEFFS_ARE_FEASIBLE():
    global FIND
    global HITBND
    global FREE1
    global FREE2
    global FREE
    global IERR
    global M
    global N
    global I
    global IBOUND
    global II
    global IP
    global ITER
    global ITMAX
    global IZ
    global IZ1
    global IZ2
    global J
    global JJ
    global JZ
    global L
    global LBOUND
    global NPP1
    global NSETP
    global INDEX
    global ZERO
    global ONE
    global TWO
    global A
    global B
    global S
    global X
    global W
    global Z
    global BND
    global ALPHA
    global ASAVE
    global CC
    global EPS
    global RANGE
    global RNORM
    global NORM
    global SM
    global SS
    global T
    global UNORM
    global UP
    global ZTEST
    global FASTNORM

    # ;
    # ;   See if each coefficient in set P is strictly interior to its constraint region.
    # ;   If so, set HITBND = false.
    # ;   If not, set HITBND = true, and also set ALPHA, JJ, and IBOUND.
    # ;   Then ALPHA will satisfy  0.  < ALPHA  <=  1.
    # ;

    ALPHA = np.float32(TWO)

    for IP in xrange(1, NSETP + 1):
        L = np.copy(INDEX[IP - 1])
        if Z[IP - 1] <= BND[0, L - 1]:
            #   Z(IP) HITS LOWER BOUND
            LBOUND = 1
        else:
            if Z[IP - 1] >= BND[1, L - 1]:
                #   Z(IP) HITS UPPER BOUND
                LBOUND = 2
            else:
                LBOUND = 0
        if LBOUND != 0:
            SSS1 = np.subtract(BND[LBOUND - 1, L - 1], X[L - 1], dtype=np.float32)
            SSS2 = np.subtract(Z[IP - 1], X[L - 1], dtype=np.float32)
            T = np.divide(SSS1, SSS2, dtype=np.float32)
            if ALPHA > T:
                ALPHA = np.copy(T)
                JJ = np.copy(IP)
                IBOUND = np.copy(LBOUND)
                # ENDIF ( LBOUND )
        # ENDIF ( ALPHA   >  T )
    IP = IP + 1  # Account for the change as in IDL
    HITBND = np.absolute(ALPHA - TWO, dtype=np.float32) > ZERO

    return  # ( SEE IF ALL CONSTRAINED COEFFS ARE FEASIBLE )


# ;----------------------------------------------------------------------
@with_goto
def TEST_SET_P_AGAINST_CONSTRAINTS():
    global FIND
    global HITBND
    global FREE1
    global FREE2
    global FREE
    global IERR
    global M
    global N
    global I
    global IBOUND
    global II
    global IP
    global ITER
    global ITMAX
    global IZ
    global IZ1
    global IZ2
    global J
    global JJ
    global JZ
    global L
    global LBOUND
    global NPP1
    global NSETP
    global INDEX
    global ZERO
    global ONE
    global TWO
    global A
    global B
    global S
    global X
    global W
    global Z
    global BND
    global ALPHA
    global ASAVE
    global CC
    global EPS
    global RANGE
    global RNORM
    global NORM
    global SM
    global SS
    global T
    global UNORM
    global UP
    global ZTEST
    global FASTNORM

    l2l = 1
    while l2l == 1:
        #   The solution obtained by solving the current set P is in the array Z().
        #

        ITER = ITER + 1
        if ITER > ITMAX:
            IERR = 4
            goto.fine_LOOPB

        # ;
        SEE_IF_ALL_CONSTRAINED_COEFFS_ARE_FEASIBLE()
        # ;
        # ;   The above call sets HITBND.  If HITBND = true THEN it also sets
        # ;   ALPHA, JJ, and IBOUND.
        if not HITBND:  # test HITBND == 0  !BUG?
            goto.fine_LOOPB

        # ;
        # ;   Here ALPHA will be between 0 and 1 for interpolation
        # ;   between the old X() and the new Z().
        for IP in xrange(1, NSETP + 1):
            L = np.copy(INDEX[IP - 1])
            SSS1 = np.subtract(Z[IP - 1], X[L - 1], dtype=np.float32)
            X[L - 1] = np.add(
                X[L - 1], np.multiply(ALPHA, SSS1, dtype=np.float32), dtype=np.float32
            )
        IP = IP + 1  # Account for the change as in IDL

        #    if ITER > 17:
        #      pdb.set_trace()
        I = np.copy(INDEX[JJ - 1])
        # ;   Note:  The exit test is done at the end of the loop, so the loop
        # ;   will always be executed at least once.

        l1l = 1
        while l1l == 1:
            #   Modify A(*,*), B(*) and the index arrays to move coefficient I
            #   from set P to set Z.
            #
            MOVE_COEF_I_FROM_SET_P_TO_SET_Z()
            #
            if NSETP <= 0:
                goto.fine_LOOPB

            # ;   See if the remaining coefficients in set P are feasible.  They should
            # ;   be because of the way ALPHA was determined.  If any are infeasible
            # ;   it is due to round-off error.  Any that are infeasible or on a boundary
            # ;   will be set to the boundary value and moved from set P to set Z.

            IBOUND = 0
            for JJ in xrange(1, NSETP + 1):
                #            if ITER > 17:
                #              pdb.set_trace()
                I = np.copy(INDEX[JJ - 1])
                if X[I - 1] <= BND[0, I - 1]:
                    IBOUND = 1
                    goto.fine_ciclo1
                else:
                    if X[I - 1] >= BND[1, I - 1]:
                        IBOUND = 2
                        goto.fine_ciclo1
            JJ = JJ + 1  # Account for the change as in IDL

            label.fine_ciclo1
            if IBOUND <= 0:
                goto.fine_ciclo2

        label.fine_ciclo2
        # ;   Copy B( ) into Z( ).  Then solve again and loop back.

        Z[0:M] = np.copy(B[0:M])
        # ;
        for I in range(NSETP, 0, -1):
            if I != NSETP:
                Z[0:I] = np.subtract(
                    Z[0:I],
                    np.multiply(A[0:I, II - 1], Z[I], dtype=np.float32),
                    dtype=np.float32,
                )
            II = np.copy(INDEX[I - 1])
            Z[I - 1] = np.divide(Z[I - 1], A[I - 1, II - 1], dtype=np.float32)
        I = I - 1  # Account for the change as in IDL

    label.fine_LOOPB

    #   The following loop can be null.
    for IP in xrange(1, NSETP + 1):
        I = np.copy(INDEX[IP - 1])
        X[I - 1] = np.copy(Z[IP - 1])
    IP = IP + 1  # Account for the change as in IDL

    return  # ( TEST SET P AGAINST CONSTRAINTS)


# ;----------------------------------------------------------------------
@with_goto
def MOVE_J_FROM_SET_Z_TO_SET_P():
    global FIND
    global HITBND
    global FREE1
    global FREE2
    global FREE
    global IERR
    global M
    global N
    global I
    global IBOUND
    global II
    global IP
    global ITER
    global ITMAX
    global IZ
    global IZ1
    global IZ2
    global J
    global JJ
    global JZ
    global L
    global LBOUND
    global NPP1
    global NSETP
    global INDEX
    global ZERO
    global ONE
    global TWO
    global A
    global B
    global S
    global X
    global W
    global Z
    global BND
    global ALPHA
    global ASAVE
    global CC
    global EPS
    global RANGE
    global RNORM
    global NORM
    global SM
    global SS
    global T
    global UNORM
    global UP
    global ZTEST
    global FASTNORM

    # ;
    # ;   The index  J=index(IZ)  has been selected to be moved from
    # ;   set Z to set P.  Z() contains the old B() adjusted as though X(J) = 0.
    # ;   A(*,J) contains the new Householder transformation vector.

    B[0:M] = np.copy(Z[0:M])
    INDEX[IZ - 1] = np.copy(INDEX[IZ1 - 1])
    INDEX[IZ1 - 1] = np.copy(J)
    IZ1 = IZ1 + 1
    NSETP = np.copy(NPP1)
    NPP1 = NPP1 + 1
    # ;   The following loop can be null or not required.

    NORM = np.copy(A[NSETP - 1, J - 1])
    A[NSETP - 1, J - 1] = np.copy(UP)
    if np.absolute(NORM, dtype=np.float32) > ZERO:
        for JZ in xrange(IZ1, IZ2 + 1):
            JJ = np.copy(INDEX[JZ - 1])
            DD1 = np.divide(A[NSETP - 1 : M, J - 1], NORM, dtype=np.float32)
            MM1 = np.multiply(DD1, A[NSETP - 1 : M, JJ - 1], dtype=np.float32)
            SM = np.sum(MM1, dtype=np.float32) / np.float32(UP)
            A[NSETP - 1 : M, JJ - 1] = np.add(
                A[NSETP - 1 : M, JJ - 1],
                np.multiply(SM, A[NSETP - 1 : M, J - 1], dtype=np.float32),
                dtype=np.float32,
            )
        JZ = JZ + 1  # Account for the change as in IDL
        A[NSETP - 1, J - 1] = np.copy(NORM)

    #   The following loop can be null.
    for L in xrange(NPP1, M + 1):
        A[L - 1, J - 1] = np.copy(ZERO)
    L = L + 1
    W[J - 1] = np.copy(ZERO)
    #   Solve the triangular system.  Store this solution temporarily in Z().
    for I in range(NSETP, 0, -1):
        if I != NSETP:
            Z[0:I] = np.subtract(
                Z[0:I],
                np.multiply(A[0:I, II - 1], Z[I], dtype=np.float32),
                dtype=np.float32,
            )
        II = np.copy(INDEX[I - 1])
        Z[I - 1] = np.divide(Z[I - 1], A[I - 1, II - 1], dtype=np.float32)
    I = I - 1  # Account for the change as in IDL

    return  # ( MOVE J FROM SET Z TO SET P )


# ----------------------------------------------------------------------
@with_goto
def TEST_COEF_J_FOR_DIAG_ELT_AND_DIRECTION_OF_CHANGE():
    global FIND
    global HITBND
    global FREE1
    global FREE2
    global FREE
    global IERR
    global M
    global N
    global I
    global IBOUND
    global II
    global IP
    global ITER
    global ITMAX
    global IZ
    global IZ1
    global IZ2
    global J
    global JJ
    global JZ
    global L
    global LBOUND
    global NPP1
    global NSETP
    global INDEX
    global ZERO
    global ONE
    global TWO
    global A
    global B
    global S
    global X
    global W
    global Z
    global BND
    global ALPHA
    global ASAVE
    global CC
    global EPS
    global RANGE
    global RNORM
    global NORM
    global SM
    global SS
    global T
    global UNORM
    global UP
    global ZTEST
    global FASTNORM

    # ;   The sign of W(J) is OK for J to be moved to set P.
    # ;   Begin the transformation and check new diagonal element to avoid
    # ;   near linear dependence.

    ASAVE = np.copy(A[NPP1 - 1, J - 1])

    # ;   Construct a Householder transformation.
    VNORM = NRM2(A[NPP1 - 1 : M, J - 1], FASTNORM)
    if A[NPP1 - 1, J - 1] > ZERO:
        VNORM = np.negative(VNORM, dtype=np.float32)
    UP = np.subtract(A[NPP1 - 1, J - 1], VNORM, dtype=np.float32)
    A[NPP1 - 1, J - 1] = np.copy(VNORM)

    if NSETP < 1:
        UNORM = np.float32(0.0)
    else:
        UNORM = NRM2(A[0:NSETP, J - 1], FASTNORM)
    if np.absolute(A[NPP1 - 1, J - 1], dtype=np.float32) > np.multiply(
        EPS, UNORM, dtype=np.float32
    ):
        # ;   Column J is sufficiently independent.  Copy b into Z, update Z.

        Z[0:M] = np.copy(B[0:M])
        # Compute product of transormation and updated right-hand side.
        NORM = np.copy(A[NPP1 - 1, J - 1])
        A[NPP1 - 1, J - 1] = np.copy(UP)
        if np.absolute(NORM, dtype=np.float32) > ZERO:
            DD1 = np.divide(A[NPP1 - 1 : M, J - 1], np.float32(NORM), dtype=np.float32)
            MM1 = np.multiply(DD1, Z[NPP1 - 1 : M], dtype=np.float32)
            SM = np.sum(MM1, dtype=np.float32) / np.float32(UP)
            Z[NPP1 - 1 : M] = np.add(
                Z[NPP1 - 1 : M],
                np.multiply(SM, A[NPP1 - 1 : M, J - 1], dtype=np.float32),
                dtype=np.float32,
            )
            A[NPP1 - 1, J - 1] = np.copy(NORM)

        if np.absolute(X[J - 1], dtype=np.float32) > ZERO:
            Z[0:NPP1] = np.add(
                Z[0:NPP1],
                np.multiply(A[0:NPP1, J - 1], X[J - 1], dtype=np.float32),
                dtype=np.float32,
            )

        # ;   Adjust Z() as though X(J) had been reset to zero.
        if FREE:
            FIND = 1
        else:
            #   Solve for ZTEST ( proposed new value for X(J) ).
            #   Then set FIND to indicate if ZTEST has moved away from X(J) in
            #   the expected direction indicated by the sign of W(J).
            ZTEST = np.divide(Z[NPP1 - 1], A[NPP1 - 1, J - 1], dtype=np.float32)
            FIND = ((W[J - 1] < ZERO) & (ZTEST < X[J - 1])) or (
                (W[J - 1] > ZERO) & (ZTEST > X[J - 1])
            )

    # ;   If J was not accepted to be moved from set Z to set P,
    # ;   restore A(NNP1,J).  Failing these tests may mean the computed
    # ;   sign of W(J) is suspect, so here we set W(J) = 0.  This will
    # ;   not affect subsequent computation, but cleans up the W() array.
    if not FIND:
        A[NPP1 - 1, J - 1] = np.float32(ASAVE)
        W[J - 1] = np.float32(ZERO)
        # ; ( .not. FIND )

    return  # ;TEST_COEF_J_FOR_DIAG_ELT_AND_DIRECTION_OF_CHANGE


# ;----------------------------------------------------------------------
@with_goto
def SELECT_ANOTHER_COEFF_TO_SOLVE_FOR():
    global FIND
    global HITBND
    global FREE1
    global FREE2
    global FREE
    global IERR
    global M
    global N
    global I
    global IBOUND
    global II
    global IP
    global ITER
    global ITMAX
    global IZ
    global IZ1
    global IZ2
    global J
    global JJ
    global JZ
    global L
    global LBOUND
    global NPP1
    global NSETP
    global INDEX
    global ZERO
    global ONE
    global TWO
    global A
    global B
    global S
    global X
    global W
    global Z
    global BND
    global ALPHA
    global ASAVE
    global CC
    global EPS
    global RANGE
    global RNORM
    global NORM
    global SM
    global SS
    global T
    global UNORM
    global UP
    global ZTEST
    global FASTNORM

    # ;   1. Search through set z for a new coefficient to solve for.
    # ;   First select a candidate that is either an unconstrained
    # ;   coefficient or ELSE a constrained coefficient that has room
    # ;   to move in the direction consistent with the sign of its dual
    #   vector component.  Components of the dual (negative gradient)
    # ;   vector will be computed as needed.
    # ;   2. For each candidate start the transformation to bring this
    # ;   candidate into the triangle, and THEN do two tests:  Test size
    # ;   of new diagonal value to avoid extreme ill-conditioning, and
    # ;   the value of this new coefficient to be sure it moved in the
    # ;   expected direction.
    # ;   3. If some coefficient passes all these conditions, set FIND = true,
    # ;   The index of the selected coefficient is J = INDEX(IZ).
    # ;   4. If no coefficient is selected, set FIND = false.

    FIND = 0
    for IZ in xrange(IZ1, IZ2 + 1):
        J = np.copy(INDEX[IZ - 1])

        # ;   Set FREE1 = true if X(J) is not at the left end-point of its
        # ;   constraint region.
        # ;   Set FREE2 = true if X(J) is not at the right end-point of its
        # ;   constraint region.
        # ;   Set FREE = true if X(J) is not at either end-point of its
        # ;   constraint region.
        # ;
        FREE1 = X[J - 1] > BND[0, J - 1]
        FREE2 = X[J - 1] < BND[1, J - 1]
        FREE = FREE1 & FREE2

        if FREE:
            TEST_COEF_J_FOR_DIAG_ELT_AND_DIRECTION_OF_CHANGE()
        else:
            #   Compute dual coefficient W(J).
            MM1 = np.multiply(A[NPP1 - 1 : M, J - 1], B[NPP1 - 1 : M], dtype=np.float32)
            W[J - 1] = np.sum(MM1, dtype=np.float32)

            #   Can X(J) move in the direction indicated by the sign of W(J)?
            if W[J - 1] < ZERO:
                if FREE1:
                    TEST_COEF_J_FOR_DIAG_ELT_AND_DIRECTION_OF_CHANGE()
            else:
                if W[J - 1] > ZERO:
                    if FREE2:
                        TEST_COEF_J_FOR_DIAG_ELT_AND_DIRECTION_OF_CHANGE()

        if FIND:
            return
    # ENDFOR;  IZ
    IZ = IZ + 1  # Account for the change as in IDL
    return  # ; ( SELECT ANOTHER COEF TO SOLVE FOR )


# ;----------------------------------------------------------------------
@with_goto
def INITIALIZE(eps1, itmax1):
    global FIND
    global HITBND
    global FREE1
    global FREE2
    global FREE
    global IERR
    global M
    global N
    global I
    global IBOUND
    global II
    global IP
    global ITER
    global ITMAX
    global IZ
    global IZ1
    global IZ2
    global J
    global JJ
    global JZ
    global L
    global LBOUND
    global NPP1
    global NSETP
    global INDEX
    global ZERO
    global ONE
    global TWO
    global A
    global B
    global S
    global X
    global W
    global Z
    global BND
    global ALPHA
    global ASAVE
    global CC
    global EPS
    global RANGE
    global RNORM
    global NORM
    global SM
    global SS
    global T
    global UNORM
    global UP
    global ZTEST
    global FASTNORM

    #  print('INITIALIZE')
    if (
        (N < 2)
        or (M < 2)
        or (len(B) != M)
        or (np.shape(BND)[0] != 2)
        or (np.shape(BND)[1] != N)
    ):
        IERR = 2
        print("Wrong input arrays size")
        sys.exit("Error!")

    IERR = 0
    if len(eps1) == 0:
        EPS = (
            np.finfo("float32")
        ).eps  # np.finfo('d').resolution  #np.finfo('f').resolution np.float32(1.19209e-07)
    else:
        EPS = eps1
    if len(itmax1) == 0:
        ITMAX = long(3) * N
    else:
        ITMAX = itmax1
    ITER = long(0)

    IZ2 = N
    IZ1 = long(1)
    NSETP = long(0)
    NPP1 = long(1)

    #   Begin:  Loop on IZ to initialize  X().
    IZ = long(IZ1)
    iiooi = 1

    while iiooi:
        if IZ > IZ2:
            goto.fine1
        J = np.copy(INDEX[IZ - 1])
        if (
            BND[0, J - 1] <= -np.finfo("float32").max
        ):  #  -np.finfo('f').max): # (1) then np.float32(-3.40282e+38)
            if (
                BND[1, J - 1] >= np.finfo("float32").max
            ):  # np.finfo('f').max): # (2) then np.float32(3.40282e+38)
                X[J - 1] = np.float32(ZERO)  # $
            else:  # (2)
                X[J - 1] = ZERO < BND[1, J - 1]
        else:  # (1)
            if (
                BND[1, J - 1] >= np.finfo("float32").max
            ):  # np.float32(3.40282e+38)): #np.finfo('f').max): #(3)
                X[J - 1] = np.float32(ZERO) > BND[0, J - 1]
            else:  # (3) #begin
                RANGE = np.subtract(BND[1, J - 1], BND[0, J - 1], dtype=np.float32)
                if RANGE <= ZERO:  # (4) begin
                    #
                    #   Here X(J) is constrained to a single value.
                    INDEX[IZ - 1] = np.copy(INDEX[IZ2 - 1])
                    INDEX[IZ2 - 1] = np.copy(J)
                    IZ = long(IZ - 1)
                    IZ2 = IZ2 - 1
                    X[J - 1] = np.copy(BND[0, J - 1])
                    W[J - 1] = np.copy(ZERO)
                else:  # endif (4) else
                    if RANGE > ZERO:  # (5)
                        #   The following statement sets X(J) to 0 if the constraint interval
                        # ;   includes 0, and otherwise sets X(J) to the endpoint of the
                        # ;   constraint interval that is closest to 0.
                        # ;
                        X[J - 1] = BND[0, J - 1] > (BND[1, J - 1] < ZERO)
                    else:  # (5) begin
                        IERR = 3
                        return
                    # endelse ; ( RANGE:.)
                # endelse

        # ;   Change B() to reflect a nonzero starting value for X(J).
        # ;
        if np.absolute(X[J - 1]) > ZERO:
            B[0:M] = np.subtract(
                B[0:M],
                np.multiply(A[0:M, J - 1], X[J - 1], dtype=np.float32),
                dtype=np.float32,
            )
        IZ = long(IZ + 1)

    label.fine1

    return
    # END ; ( INITIALIZE )


# ;----------------------------------------------------------------------
@with_goto
def BVLS(A1, B1, BND1):
    global FIND
    global HITBND
    global FREE1
    global FREE2
    global FREE
    global IERR
    global M
    global N
    global I
    global IBOUND
    global II
    global IP
    global ITER
    global ITMAX
    global IZ
    global IZ1
    global IZ2
    global J
    global JJ
    global JZ
    global L
    global LBOUND
    global NPP1
    global NSETP
    global INDEX
    global ZERO
    global ONE
    global TWO
    global A
    global B
    global S
    global X
    global W
    global Z
    global BND
    global ALPHA
    global ASAVE
    global CC
    global EPS
    global RANGE
    global RNORM
    global NORM
    global SM
    global SS
    global T
    global UNORM
    global UP
    global ZTEST
    global FASTNORM

    # Load needed input parameters into the COMMON block
    # ;

    #  print('BVLS')
    A = np.copy(A1)
    B = np.copy(B1)
    BND = np.copy(BND1)

    siz = np.shape(A)
    M = siz[0]
    N = siz[1]

    X = np.zeros(N, dtype=np.float32)
    W = np.zeros(N, dtype=np.float32)
    INDEX = np.arange(N, dtype=np.long) + 1

    S = np.zeros(N, dtype=np.float32)
    Z = np.zeros(M, dtype=np.float32)
    eps1 = []
    itmax1 = []
    FASTNORM1 = False

    # Load some constants into the COMMON block
    #
    ZERO = np.float32(0.0)
    ONE = np.float32(1.0)
    TWO = np.float32(2.0)
    if FASTNORM1:
        FASTNORM = True
    else:
        FASTNORM = False

    INITIALIZE(eps1, itmax1)

    #   The above call will set IERR.
    #
    grrr = 1
    while grrr:
        #    ;   Quit on error flag, or if all coefficients are already in the
        #    ;   solution, .or. if M columns of A have been triangularized.
        if (IERR != 0) or (IZ1 > IZ2) or (NSETP >= M):
            goto.fine
        else:
            SELECT_ANOTHER_COEFF_TO_SOLVE_FOR()

            #    ;
            #    ;   See if no index was found to be moved from set Z to set P.
            #   ;   Then go to termination.
            if FIND == 0:
                goto.fine

            MOVE_J_FROM_SET_Z_TO_SET_P()

            TEST_SET_P_AGAINST_CONSTRAINTS()

    #    ;   The above call may set IERR.
    #    ;   All coefficients in set P are strictly feasible.  Loop back.

    # ENDWHILE

    label.fine

    TERMINATION()
    A1 = np.copy(A)
    B1 = np.copy(B)
    BND1 = np.copy(BND)
    X1 = np.copy(X)
    RNORM1 = RNORM
    NSETP1 = NSETP
    W1 = np.copy(W)
    INDEX1 = np.copy(INDEX)
    IERR1 = IERR
    ITER1 = ITER
    return X1


# ;----------------------------------------------------------------------