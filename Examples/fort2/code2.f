       PROGRAM P
       CALL YACSINIT()
       END

       SUBROUTINE SERV1(compo,a,b,c)
       include 'calcium.hf'
       integer compo(2),nval
       real*8 tt,t0,t1,a,b,c
       write(6,*)a,b
       CALL cplDB(compo,CP_ITERATION,t0,t1,1,'PARAM',1,nval,tt,info)
       write(6,*)'info=',info
       write(6,*)'tt=',tt
       c=a+b
       return 
       end
