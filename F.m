clc;
clear all;
%% 读取数据
filename = 'data/Data A-Flight.csv'; %文件

[~,DptrDD] = xlsread(filename,1,'B2:B207');%读取
DptrT = xlsread(filename,1,'C2:C207');%读取
[~,DptrStnn] = xlsread(filename,1,'D2:D207');%读取
[~,ArrvDD] = xlsread(filename,1,'E2:E207');%读取
ArrvT = xlsread(filename,1,'F2:F207');%读取
[~,ArrvStnn] = xlsread(filename,1,'G2:G207');%读取

NumOfFli=length(DptrT); %flight 数量
DptrD=zeros(NumOfFli,1);
ArrvD=zeros(NumOfFli,1);
FlightT=zeros(NumOfFli,1);
StnTableA={"NKX" "CTH" "PDK" "PGX" "PLM" "PXB" "XGS"};
FlightStn=zeros(NumOfFli,2);
NumOfStn=length(StnTableA);

for i=1:NumOfFli
    Temp=strsplit(DptrDD{i},'/');
    DptrD(i)=str2double(Temp{2});
    Temp=strsplit(ArrvDD{i},'/');
    ArrvD(i)=str2double(Temp{2});
end
ArrvD=ArrvD-min(DptrD)+1;
DptrD=DptrD-min(DptrD)+1;
NumOfD=max(DptrD);

for i=1:NumOfFli
    if DptrD(i)==ArrvD(i)
        FlightT(i)=round((ArrvT(i)-DptrT(i))*24*60);
    elseif DptrD(i)+1==ArrvD(i)
        FlightT(i)=round((ArrvT(i)-DptrT(i)+1)*24*60);
    else
        print("错误 1");
    end
end

for i=1:NumOfFli
    if DptrT(i)<ArrvT(i)
        ArrvT(i)=round(ArrvT(i)*24*60);
        DptrT(i)=round(DptrT(i)*24*60);
    elseif DptrT(i)>ArrvT(i)
        ArrvT(i)=round((ArrvT(i)+1)*24*60);
        DptrT(i)=round(DptrT(i)*24*60);
    end
end

for i=1:NumOfFli
    for i2= 1:NumOfStn
        if DptrStnn{i}==StnTableA{i2}
            FlightStn(i,1)=i2;
        end
        if ArrvStnn{i}==StnTableA{i2}
            FlightStn(i,2)=i2;
        end
    end
end

%A 数据
StnPop=zeros(NumOfStn,3); %各个机场现有人员数量,1 列为正，2 列为皆可，3列为副
StnPop(1,:)=[5,6,10];


MaxBlk=660;
MaxDP=720;

%% 初始化
group=cell(NumOfD,1);
Duty=cell(NumOfD,1);
DutySingle=cell(NumOfD,1);
DutyPlus=cell(NumOfD,1);
NumOfTheDay=zeros(NumOfD,1);
NumOfGroup=zeros(NumOfD,1);
NumOfDuty=zeros(NumOfD,1);
NumOfDutySingle=zeros(NumOfD,1);
NumOfDutyPlus=zeros(NumOfD,1);
TheDayTable=cell(NumOfD,1);
TDT=cell(NumOfD,1);
chengjiNum=zeros(NumOfFli,1);

for d=1:NumOfD
    %生成该天要做的航段任务表
    findex=find(DptrD==d);
    NumOfTheDay(d)=length(findex);
    TheDayTable{d}=zeros(NumOfTheDay(d),5);
    TheDayTable{d}(:,1)=findex;
    TheDayTable{d}(:,[2,3])=FlightStn(findex,:);
    TheDayTable{d}(:,4)=DptrT(findex,:);
    TheDayTable{d}(:,5)=ArrvT(findex,:);
    TheDayTable{d}(:,6)=FlightT(findex,:);

    TDT{d}=cell(NumOfStn,1);
    for i=1: NumOfStn
        TDT{d}{i}=TheDayTable{d}(TheDayTable{d}(:,2)==i,:);
    end
end

%% 生成组 group

usedid=cell(NumOfD,1);
for d=1:NumOfD
    for i= 1:size(TDT{d}{1},1)
        targetstn=TDT{d}{1}(i,3);
        findgroup=0;
        findgroup2=0;
        for i2= 1:size(TDT{d}{targetstn},1)
            if TDT{d}{targetstn}(i2,3)~=1
                continue
            end
            jiangeT=TDT{d}{targetstn}(i2,4)-TDT{d}{1}(i,5);
            if jiangeT==40
                NumOfGroup(d)=NumOfGroup(d)+1;
                group{d}{NumOfGroup(d),1}=[TDT{d}{1}(i,:);TDT{d}{targetstn}(i2,:)];
                group{d}{1,2}(NumOfGroup(d),:)=[TDT{d}{1}(i,1),TDT{d}{targetstn}(i2,1),...
                    TDT{d}{1}(i,4),TDT{d}{targetstn}(i2,5),jiangeT];
                usedid{d}=[usedid{d},group{d}{1,2}(NumOfGroup(d),[1,2])];
                findgroup=findgroup+1;
                break;
            elseif jiangeT>=40&&jiangeT<=45
                tempgroup1=[TDT{d}{1}(i,:);TDT{d}{targetstn}(i2,:)];
                tempgroup2=[TDT{d}{1}(i,1),TDT{d}{targetstn}(i2,1),...
                    TDT{d}{1}(i,4),TDT{d}{targetstn}(i2,5),jiangeT];
                findgroup2=findgroup2+1;
            end
        end
        if findgroup==0&&findgroup2>=1
            NumOfGroup(d)=NumOfGroup(d)+1;
            group{d}{NumOfGroup(d),1}=tempgroup1;
            group{d}{1,2}(NumOfGroup(d),:)=tempgroup2;
            usedid{d}=[usedid{d},group{d}{1,2}(NumOfGroup(d),[1,2])];
        end
    end
end

%% 生成 duty
for d=1:NumOfD
    Duty{d}=cell(1,1);
    [~,gweizhi]=sort(group{d}{1,2}(:,3));
    usedgroup=zeros(1,NumOfGroup(d))+1; %1 是还没用，可用
    for i=1:NumOfGroup(d)
        if usedgroup(gweizhi(i))~=0
            nowi=i;
            NumOfDuty(d)=NumOfDuty(d)+1;
            usedgroup(gweizhi(i))=0;
            Duty{d}{NumOfDuty(d),1}=[];
            Duty{d}{NumOfDuty(d),1}=[Duty{d}{NumOfDuty(d),1};group{d}{gweizhi(i),1}];
            Duty{d}{NumOfDuty(d),2}(1,1)=group{d}{gweizhi(i),1}(1,4);
            Duty{d}{NumOfDuty(d),2}(1,2)=group{d}{gweizhi(i),1}(2,5);
            Duty{d}{NumOfDuty(d),2}(1,3)=group{d}{gweizhi(i),1}(2,4)-...
                group{d}{gweizhi(i),1}(1,5);
            Duty{d}{NumOfDuty(d),2}(1,4)=Duty{d}{NumOfDuty(d),2}(1,2)-...
                Duty{d}{NumOfDuty(d),2}(1,1)-Duty{d}{NumOfDuty(d),2}(1,3);
            for i2=i+1:NumOfGroup(d)
                if (group{d}{1,2}(gweizhi(nowi),4)-group{d}{1,2}(gweizhi(i2),3)==-40 )...
                        &&group{d}{gweizhi(i2),1}(2,5)-Duty{d}{NumOfDuty(d),2}(1)<=720
                    usedgroup(gweizhi(i2))=0;
                    Duty{d}{NumOfDuty(d),1}=[Duty{d}{NumOfDuty(d),1};group{d}{gweizhi(i2),1}];
                    Duty{d}{NumOfDuty(d),2}(1,2)=group{d}{gweizhi(i2),1}(2,5);
                    Duty{d}{NumOfDuty(d),2}(1,3)=Duty{d}{NumOfDuty(d),2}(1,3)+...
                        group{d}{gweizhi(i2),1}(2,4)-group{d}{gweizhi(i2),1}(1,5)...
                        +group{d}{gweizhi(i2),1}(1,4)-group{d}{gweizhi(i),1}(2,5);
                    Duty{d}{NumOfDuty(d),2}(1,4)=Duty{d}{NumOfDuty(d),2}(1,2)-...
                        Duty{d}{NumOfDuty(d),2}(1,1)-Duty{d}{NumOfDuty(d),2}(1,3);
                    nowi=i2;
                end
            end
        end
    end
end

%% dutysigle&&dutyplus
for d=1:NumOfD
    usedid{d}=sort(usedid{d});
    for i=1:NumOfTheDay(d)
        if sum(TheDayTable{d}(i,1)==usedid{d})==0
            NumOfDutySingle(d)=NumOfDutySingle(d)+1;

            DutySingle{d}(NumOfDutySingle(d),:)=TheDayTable{d}(i,:);
        end
    end
end

bixushangci=cell(NumOfD,1);
for d=1:NumOfD
    if NumOfDutySingle(d)>0
        bixushangci{d}=zeros(1,NumOfDutySingle(d))+1;
        for i=1:NumOfDutySingle(d) %找必须上次
            X=DutySingle{d}(i,2);
            toX=find(TheDayTable{d}(:,3)==X);
            toXNum=length(toX);
            for i2=1:toXNum
                if DutySingle{d}(i,4)-TheDayTable{d}(toX(i2),5)>=40
                    bixushangci{d}(i)=0;
                end
            end
        end

        for i=1:NumOfDutySingle(d)
            if bixushangci{d}(i)==1 %先做上次必须
                X=DutySingle{d}(i,2);
                YtoX=find(TheDayTable{d-1}(:,3)==X);
                YtoXNum=length(YtoX);
                over=0;
                [~,YtoXID]=sort(TheDayTable{d-1}(YtoX,6));
                for i2=1:YtoXNum
                    if chengjiNum(TheDayTable{d-1}(YtoX(YtoXID(i2)),1))<=3
                        chengjiNum(TheDayTable{d-1}(YtoX(YtoXID(i2)),1))=chengjiNum(TheDayTable{d-1}(YtoX(YtoXID(i2)),1))+2;
                        NumOfDutyPlus(d-1)=NumOfDutyPlus(d-1)+1;
                        DutyPlus{d-1}(NumOfDutyPlus(d-1),:)=zeros(1,8);
                        DutyPlus{d-1}(NumOfDutyPlus(d-1),[1:6])=TheDayTable{d-1}(YtoX(YtoXID(i2)),:);
                        DutyPlus{d-1}(NumOfDutyPlus(d-1),7)=1;
                        DutyPlus{d-1}(NumOfDutyPlus(d-1),8)=1;
                        NumOfDutyPlus(d)=NumOfDutyPlus(d)+1;
                        DutyPlus{d}(NumOfDutyPlus(d),:)=zeros(1,8);
                        DutyPlus{d}(NumOfDutyPlus(d),[1:6])=DutySingle{d}(i,:);
                        DutyPlus{d}(NumOfDutyPlus(d),7)=2;
                        DutyPlus{d}(NumOfDutyPlus(d),8)=1;
                        over=1;
                        break;
                    end
                end
                if over==0
                    print("error2")
                end
            end
        end

        for i=1:NumOfDutySingle(d)
            if bixushangci{d}(i)==0 %后坐无所谓的
                X=DutySingle{d}(i,2);
                YtoX=find(TheDayTable{d-1}(:,3)==X);
                YtoXNum=length(YtoX);
                over=0;
                [~,YtoXID]=sort(TheDayTable{d-1}(YtoX,6));
                for i2=1:YtoXNum
                    if chengjiNum(TheDayTable{d-1}(YtoX(YtoXID(i2)),1))<=3
                        chengjiNum(TheDayTable{d-1}(YtoX(YtoXID(i2)),1))=chengjiNum(TheDayTable{d-1}(YtoX(YtoXID(i2)),1))+2;
                        NumOfDutyPlus(d-1)=NumOfDutyPlus(d-1)+1;
                        DutyPlus{d-1}(NumOfDutyPlus(d-1),:)=zeros(1,8);
                        DutyPlus{d-1}(NumOfDutyPlus(d-1),[1:6])=TheDayTable{d-1}(YtoX(YtoXID(i2)),:);
                        DutyPlus{d-1}(NumOfDutyPlus(d-1),7)=1;
                        DutyPlus{d-1}(NumOfDutyPlus(d-1),8)=0;
                        NumOfDutyPlus(d)=NumOfDutyPlus(d)+1;
                        DutyPlus{d}(NumOfDutyPlus(d),:)=zeros(1,8);
                        DutyPlus{d}(NumOfDutyPlus(d),[1:6])=DutySingle{d}(i,:);
                        DutyPlus{d}(NumOfDutyPlus(d),7)=2;
                        DutyPlus{d}(NumOfDutyPlus(d),8)=1;
                        over=1;
                        break;
                    end
                end
                if over==0
                    print("error2")
                end
            end
        end


    end
end

%% 第三问
P=10;
global pstatus
pstatus=zeros(P,NumOfD);
global Pstatus
Pstatus=zeros(4,P); %已执勤几天，已在环几天，已休息的第几天,是否可用(0休息，1 环中还可以工作，2 休息好未工作)
Pstatus(3,:)=zeros(1,P)+2;
Pstatus(4,:)=zeros(1,P)+2;
pable=sum(Pstatus(4,:)>0);
global pold
global poldnum
pold=zeros(5,P); %01,p 是否已工作 x 天
poldnum=zeros(4,1);

abletoplus=NumOfGroup-NumOfDuty;
realplus=zeros(NumOfD,1);

for i=1:3
    pold(i,:)=(Pstatus(4,:)==1).*(Pstatus(1,:)==i);
    poldnum(i)=sum(pold(i,:));
end
pold(4,:)=Pstatus(4,:)==2;
poldnum(4)=sum(pold(4,:));
pold(5,:)=(Pstatus(4,:)==1).*(Pstatus(1,:)==0);
poldnum(5)=sum(pold(5,:));

fenpei=zeros(d,P);
for d=1:NumOfD
    if NumOfDutyPlus(d)>0
        knum=sum(DutyPlus{d}(:,7)==1);
        tiqiannum=0;
        index=find(pold(2,:)==1);
        for i=1:poldnum(2)
            if fenpei(d,index(i))~=1
                setp(index(i),d)
                fenpei(d,index(i))=1;
                setp(index(i),d+1)
                fenpei(d+1,index(i))=1;
                tiqiannum=tiqiannum+1;
                if tiqiannum==knum
                    break;
                end
            end
        end
        if tiqiannum<knum
            index=find(pold(1,:)==1);
            for i=1:poldnum(1)
                if fenpei(d,index(i))~=1
                    setp(index(i),d)
                    fenpei(d,index(i))=1;
                    setp(index(i),d+1)
                    fenpei(d+1,index(i))=1;
                    tiqiannum=tiqiannum+1;
                    if tiqiannum==knum
                        break;
                    end
                end
            end
        end
        if tiqiannum<knum
            index=find(pold(4,:)==1);
            for i=1:poldnum(4)
                if fenpei(d,index(i))~=1
                    setp(index(i),d)
                    fenpei(d,index(i))=1;
                    setp(index(i),d+1)
                    fenpei(d+1,index(i))=1;
                    tiqiannum=tiqiannum+1;
                    if tiqiannum==knum
                        break;
                    end
                end
            end
        end
        if tiqiannum<knum
            disp("error5")
        end

    end

    % 剩下的全是单体
    donum=0;
    if donum<NumOfGroup(d)
        index=find(pold(1,:)==1);
        for i=1:poldnum(1)
            if fenpei(d,index(i))~=1
                setp(index(i),d)
                fenpei(d,index(i))=1;
                donum=donum+1;
                if donum==NumOfGroup(d)
                    break;
                end
            end
        end
    end

    if donum<NumOfGroup(d)
        index=find(pold(2,:)==1);
        for i=1:poldnum(2)
            if fenpei(d,index(i))~=1
                setp(index(i),d)
                fenpei(d,index(i))=1;
                donum=donum+1;
                if donum==NumOfGroup(d)
                    break;
                end
            end
        end
    end

    if donum<NumOfGroup(d)
        index=find(pold(3,:)==1);
        for i=1:poldnum(3)
            if fenpei(d,index(i))~=1
                setp(index(i),d)
                fenpei(d,index(i))=1;
                donum=donum+1;
                if donum==NumOfGroup(d)
                    break;
                end
            end
        end
    end

    if donum<NumOfGroup(d)
        index=find(pold(5,:)==1);
        for i=1:poldnum(5)
            if fenpei(d,index(i))~=1
                setp(index(i),d)
                fenpei(d,index(i))=1;
                donum=donum+1;
                if donum==NumOfGroup(d)
                    break;
                end
            end
        end
    end

    if donum<NumOfGroup(d)
        index=find(pold(4,:)==1);
        for i=1:poldnum(4)
            if fenpei(d,index(i))~=1
                setp(index(i),d)
                fenpei(d,index(i))=1;
                donum=donum+1;
                if donum==NumOfGroup(d)
                    break;
                end
            end
        end
    end

    if donum<NumOfDuty(d)
        disp("error6")
    else
        realplus(d)=donum-NumOfDuty(d);
    end

    %其他休息
    for p=1:P
        if fenpei(d,p)==0
            restp(p,d)
            fenpei(d,p)=1;
        end
    end

end

%% 算时间
chengjitime=0;
for d=1:NumOfD
    if NumOfDutyPlus(d)>0
        for i=1:NumOfDutyPlus(d)
            if DutyPlus{d}(i,7)==1
                chengjitime=chengjitime+DutyPlus{d}(i,6);
            end
        end
    end
end
lianjietime=0;
for d=1:NumOfD
    if NumOfDuty(d)>0
        for i=1:NumOfDuty(d)
            lianjietime=lianjietime+Duty{d}{i,2}(3);
        end
    end
end
lianjietime=lianjietime-sum(realplus)*40;
ftime=sum(FlightT);
liyonglv=ftime/(ftime+lianjietime+chengjitime);
dutycost=((ftime+lianjietime+chengjitime)/60)*(640+600);

%% 真实 duty

Duty=cell(NumOfD,1);
NumOfDuty=zeros(NumOfD,1);
for d=1:NumOfD
    finalplus=0;
    Duty{d}=cell(1,1);
    [~,gweizhi]=sort(group{d}{1,2}(:,3));
    usedgroup=zeros(1,NumOfGroup(d))+1; %1 是还没用，可用
    for i=1:NumOfGroup(d)
        if usedgroup(gweizhi(i))~=0
            nowi=i;
            NumOfDuty(d)=NumOfDuty(d)+1;
            usedgroup(gweizhi(i))=0;
            Duty{d}{NumOfDuty(d),1}=[];
            Duty{d}{NumOfDuty(d),1}=[Duty{d}{NumOfDuty(d),1};group{d}{gweizhi(i),1}];
            Duty{d}{NumOfDuty(d),2}(1,1)=group{d}{gweizhi(i),1}(1,4);
            Duty{d}{NumOfDuty(d),2}(1,2)=group{d}{gweizhi(i),1}(2,5);
            Duty{d}{NumOfDuty(d),2}(1,3)=group{d}{gweizhi(i),1}(2,4)-...
                group{d}{gweizhi(i),1}(1,5);
            Duty{d}{NumOfDuty(d),2}(1,4)=Duty{d}{NumOfDuty(d),2}(1,2)-...
                Duty{d}{NumOfDuty(d),2}(1,1)-Duty{d}{NumOfDuty(d),2}(1,3);
            for i2=i+1:NumOfGroup(d)
                if (group{d}{1,2}(gweizhi(nowi),4)-group{d}{1,2}(gweizhi(i2),3)==-40 )...
                        &&group{d}{gweizhi(i2),1}(2,5)-Duty{d}{NumOfDuty(d),2}(1)<=720 ...
                        && finalplus<(abletoplus(d)-realplus(d))
                    usedgroup(gweizhi(i2))=0;
                    Duty{d}{NumOfDuty(d),1}=[Duty{d}{NumOfDuty(d),1};group{d}{gweizhi(i2),1}];
                    Duty{d}{NumOfDuty(d),2}(1,2)=group{d}{gweizhi(i2),1}(2,5);
                    Duty{d}{NumOfDuty(d),2}(1,3)=Duty{d}{NumOfDuty(d),2}(1,3)+...
                        group{d}{gweizhi(i2),1}(2,4)-group{d}{gweizhi(i2),1}(1,5)...
                        +group{d}{gweizhi(i2),1}(1,4)-group{d}{gweizhi(i),1}(2,5);
                    Duty{d}{NumOfDuty(d),2}(1,4)=Duty{d}{NumOfDuty(d),2}(1,2)-...
                        Duty{d}{NumOfDuty(d),2}(1,1)-Duty{d}{NumOfDuty(d),2}(1,3);
                    nowi=i2;
                    finalplus=finalplus+1;
                end
            end
        end
    end
end

%% jisuan2
allnum=sum(NumOfDuty)+sum(NumOfDutyPlus);
alldutytime=zeros(allnum,1);
allflighttime=zeros(allnum,1);
k=0;
for d=1:NumOfD
    for i=1:NumOfDuty(d)
        k=k+1;
        allflighttime(k)=Duty{d}{i,2}(4);
        alldutytime(k)=Duty{d}{i,2}(4)+Duty{d}{i,2}(3);
    end
    for i=1:NumOfDutyPlus(d)
        k=k+1;
        allflighttime(k)=DutyPlus{d}(i,6);
        alldutytime(k)=DutyPlus{d}(i,6);
    end
end

answer6=[min(allflighttime),mean(allflighttime),max(allflighttime)];
answer7=[min(alldutytime),mean(alldutytime),max(alldutytime)];
answer6=answer6/60;
answer7=answer7/60;

dutytianshu=sum(pstatus,2);
answer8=[min(dutytianshu),sum(dutytianshu)*2/21,max(dutytianshu)];

%% 计算环数量
huanlx=zeros(P,4);
for p=1:P
    do=0;
    for d=1:NumOfD-1
        if pstatus(p,d)==1
            do=do+1;
        elseif pstatus(p,d)==0 && pstatus(p,max(d-1,1))==1
            huanlx(p,do)=huanlx(p,do)+1;
            do=0;
        end
    end
    d= NumOfD;
    if pstatus(p,d)==1
        do=do+1;
        huanlx(p,do)=huanlx(p,do)+1;
    elseif pstatus(p,d)==0 && pstatus(p,max(d-1,1))==1
        huanlx(p,do)=huanlx(p,do)+1;
        do=0;
    end
end
answer9=sum(huanlx);

%% huan
scofp=cell(P,1);
huannumofp=zeros(P,1);
d=1;
for p=1:P
    if pstatus(p,d)==1
        scofp{p}=zeros(1,3);
        scofp{p}(1,1)=1;
        huannumofp(p)=1;
    end
end
for p=1:P
    do=huannumofp(p);
    if p==4
        1;
    end
    for d=2:NumOfD-1
        if pstatus(p,d)==1&&pstatus(p,d-1)==0&&pstatus(p,max(d-2,1))==0
            do=1;
            huannumofp(p)=huannumofp(p)+1;
            scofp{p}(huannumofp(p),:)=zeros(1,3);
            scofp{p}(huannumofp(p),1)=d;
        elseif pstatus(p,d)==0 && pstatus(p,d-1)==0&&huannumofp(p)~=0&&scofp{p}(huannumofp(p),3)==0
            if d~=2
                scofp{p}(huannumofp(p),2)=d-2;
                scofp{p}(huannumofp(p),3)=do;
                do=0;
            end
        elseif pstatus(p,d)==1&&pstatus(p,d-1)==0&&pstatus(p,max(d-2,1))==1
            do=do+2;
        elseif pstatus(p,d)==1
            do=do+1;
        elseif pstatus(p,d)==0
            do=do;
        else
            disp("error8");
        end
    end

    d=NumOfD;
    if pstatus(p,d)==1&&pstatus(p,d-1)==0&&pstatus(p,max(d-2,1))==0
        do=1;
        huannumofp(p)=huannumofp(p)+1;
        scofp{p}(huannumofp(p),:)=zeros(1,3);
        scofp{p}(huannumofp(p),1)=d;
        scofp{p}(huannumofp(p),2)=d;
        scofp{p}(huannumofp(p),3)=1;
    elseif pstatus(p,d)==0 && pstatus(p,d-1)==0&&huannumofp(p)~=0&&scofp{p}(huannumofp(p),3)==0
        if d~=2
            scofp{p}(huannumofp(p),2)=d-2;
            scofp{p}(huannumofp(p),3)=do;
            do=0;
        end
    elseif pstatus(p,d)==1&&pstatus(p,d-1)==0&&pstatus(p,max(d-2,1))==1
        do=do+2;
        scofp{p}(huannumofp(p),2)=d;
        scofp{p}(huannumofp(p),3)=do;
    elseif pstatus(p,d)==1
        do=do+1;
        scofp{p}(huannumofp(p),2)=d;
        scofp{p}(huannumofp(p),3)=do;
    elseif pstatus(p,d)==0
        do=do;
        scofp{p}(huannumofp(p),2)=d-1;
        scofp{p}(huannumofp(p),3)=do;
    else
        disp("error9");
    end
end

startday=zeros(NumOfD,1);
endday=zeros(NumOfD,1);
huantime=0;
for p=1:P
    huantime=huantime+(sum(scofp{p}(:,3))-length(scofp{p}(:,3)))*12*60;
    for i=1:length(scofp{p}(:,3))
        startday(scofp{p}(i,1))=startday(scofp{p}(i,1))+1;
        endday(scofp{p}(i,2))=endday(scofp{p}(i,2))+1;
    end
end

%找结束时间的最早值减去开始时间的最晚值
daystarttime=cell(NumOfD,1);
dayendtime=cell(NumOfD,1);
daydutytime=cell(NumOfD,1);
for d=1:NumOfD
    l1=0;
    l2=0;
    l=0;
    for i=1:NumOfDuty(d)
        l1=l1+1;
        l2=l2+1;
        l=l+1;
        daydutytime{d}(l,1)=Duty{d}{i,2}(2)-Duty{d}{i,2}(1);
        daystarttime{d}(l1,1)=Duty{d}{i,2}(1);
        dayendtime{d}(l2,1)=Duty{d}{i,2}(2);
    end
    for i=1:NumOfDutyPlus(d)
        l=l+1;
        daydutytime{d}(l,1)=DutyPlus{d}(i,6);
        if DutyPlus{d}(i,7)==1
            l1=l1+1;
            daystarttime{d}(l1,1)=DutyPlus{d}(i,4);
        elseif DutyPlus{d}(i,7)==2
            l2=l2+1;
            dayendtime{d}(l2,1)=DutyPlus{d}(i,5);
        end
    end
end
for d=1:NumOfD
    daystarttime{d}=sort(daystarttime{d},'descend');
    dayendtime{d}=sort(dayendtime{d});
    daydutytime{d}=sort(daydutytime{d});
    if startday(d)>0
        huantime=huantime-sum(daystarttime{d}([1:startday(d)]));
    end
    if endday(d)>0
        huantime=huantime+sum(dayendtime{d}([1:endday(d)]));
    end
end

huancost=huantime/60*20;

dutycostplusD=sum(pstatus([7:10],:));
for d=1:NumOfD
    dutycost=dutycost+sum(daydutytime{d}([1:dutycostplusD(d)]))/60*40;
end

%shuchu=cell();


function setp(p,d)
global pstatus
global Pstatus
global pold
global poldnum
pstatus(p,d)=1;
if sum(Pstatus(:,p)==[0;0;2;2])==4
    Pstatus(:,p)=[1;1;0;1];
    %工作中
elseif sum(Pstatus([3,4],p)==[0;1])==2&&Pstatus(1,p)~=3&&Pstatus(2,p)==9
    Pstatus(:,p)=[Pstatus(1,p)+1;Pstatus(2,p)+1;0;0];
elseif sum(Pstatus([3,4],p)==[0;1])==2&&Pstatus(1,p)~=3
    Pstatus(:,p)=[Pstatus(1,p)+1;Pstatus(2,p)+1;0;1];
elseif sum(Pstatus([3,4],p)==[0;1])==2&&Pstatus(1,p)==3
    Pstatus(:,p)=[Pstatus(1,p)+1;Pstatus(2,p)+1;0;0];
    %休息一天
elseif sum(Pstatus(:,p)==[0;9;1;1])==4
    Pstatus(:,p)=[1;10;0;0];
elseif sum(Pstatus([3,4],p)==[1;1])==2
    Pstatus(:,p)=[1;Pstatus(2,p)+1;0;1];

else
    disp("error3")
end

for i=1:3
    pold(i,:)=(Pstatus(4,:)==1).*(Pstatus(1,:)==i);
    poldnum(i)=sum(pold(i,:));
end
pold(4,:)=Pstatus(4,:)==2;
poldnum(4)=sum(pold(4,:));
pold(5,:)=(Pstatus(4,:)==1).*(Pstatus(1,:)==0);
poldnum(5)=sum(pold(5,:));
end

function restp(p,d)
global pstatus
global Pstatus
global pold
global poldnum
pstatus(p,d)=0;
if sum(Pstatus(:,p)== [0;0;2;2])==4
    Pstatus(:,p)=[0;0;2;2];

elseif Pstatus(3,p)==1
    Pstatus(:,p)=[0;0;2;2];
elseif Pstatus(2,p)==10
    Pstatus(:,p)=[0;0;1;0];

elseif Pstatus(3,p)==0&&Pstatus(2,p)==9
    Pstatus(:,p)=[0;0;1;0];
elseif Pstatus(3,p)==0
    Pstatus(:,p)=[0;Pstatus(2,p)+1;1;1];
else
    print("error4")
end

for i=1:3
    pold(i,:)=(Pstatus(4,:)==1).*(Pstatus(1,:)==i);
    poldnum(i)=sum(pold(i,:));
end
pold(4,:)=Pstatus(4,:)==2;
poldnum(4)=sum(pold(4,:));
pold(5,:)=(Pstatus(4,:)==1).*(Pstatus(1,:)==0);
poldnum(5)=sum(pold(5,:));

end


