       SUBROUTINE SERV1(compo,a,b,c)
       include 'calcium.hf'
       integer compo(2)
       real*8 tt,a,b,c
       write(6,*)a,b
       tt=125.45
       CALL cpeDB(compo,CP_ITERATION,0.,1,'PARAM',1,tt,info)
       write(6,*)'info=',info
       c=a+b
       return 
       end
