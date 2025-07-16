%% Data organization

% Prompt user to select one or more CSV files
[fileNames, pathName] = uigetfile('*.csv', 'Select CSV file(s)', 'MultiSelect', 'on');

% Ensure fileNames is a cell array for consistency
if ischar(fileNames)
    fileNames = {fileNames};
end

trialNum = length(fileNames);
allData= {};
material_vector = zeros(trialNum,1);

for fileIdx = 1:trialNum
    fullFilePath = fullfile(pathName, fileNames{fileIdx});

    %determine tag - hard or soft ball
    if contains(fileNames{fileIdx},'soft')
        material = 0;
    elseif contains(fileNames{fileIdx},'hard')
        material = 1;
    end

    material_vector(fileIdx) = material; 

    %stack all data matrices
    dataRead = readmatrix(fullFilePath);

    allData{end+1} = dataRead;

end 

%% Feature extraction

featureVector = zeros(trialNum,3);

for i = 1:trialNum

    sensor1 = allData{i}(:,1);
    sensor2 = allData{i}(:,2);

    %max force
    max_s1 = max(max(sensor1),1);
    max_s2 = max(max(sensor2),1);

    %ratio of max forces
    rat_s1_s2 = max_s1/max_s2;

    featureVector(i,:) = [max_s1,max_s2,rat_s1_s2];
    
end

save('material_vector.mat', 'material_vector');
save('featureVector.mat', 'featureVector');

%% Modeling & Classification

% divide data into training and testing set

k=10;
%LDA model
LDAModel = fitcdiscr(featureVector, material_vector,'DiscrimType', 'linear','Gamma', 0.5); 
CVLDAModel = crossval(LDAModel, 'KFold', k);
cvLossLDA = kfoldLoss(CVLDAModel);
fprintf('LDA linear MCR: %.2f\n', cvLossLDA);


% SVM linear
SVMModel = fitcsvm(featureVector, material_vector, 'KernelFunction', 'linear', 'Standardize', true);
CVSVMModel = crossval(SVMModel, 'KFold', k);
cvLossSVM = kfoldLoss(CVSVMModel);
%fprintf('SVM linear kernel MCR: %.2f\n', cvLossSVM);