CREATE DATABASE `CompanyInformation` DEFAULT CHARACTER SET utf8 ;

CREATE  TABLE `companyinformation`.`CompanyName` (
  `idCompanyName` CHAR(19) NOT NULL ,
  PRIMARY KEY (`idCompanyName`) ,
  UNIQUE INDEX `idCompanyName_UNIQUE` (`idCompanyName` ASC) )
DEFAULT CHARACTER SET = utf8;

ALTER TABLE `companyinformation`.`companyname` ADD COLUMN `companyname` VARCHAR(100) NOT NULL  AFTER `ID` , ADD COLUMN `introduction` VARCHAR(2048) NULL  AFTER `companyname` , ADD COLUMN `product` VARCHAR(300) NULL  AFTER `introduction` , ADD COLUMN `website` VARCHAR(100) NULL  AFTER `product` , ADD COLUMN `websitetitle` VARCHAR(150) NULL  AFTER `website` , CHANGE COLUMN `idCompanyName` `ID` CHAR(19) NOT NULL  
, DROP PRIMARY KEY 
, ADD PRIMARY KEY (`ID`) 
, DROP INDEX `idCompanyName_UNIQUE` 
, ADD UNIQUE INDEX `idCompanyName_UNIQUE` (`ID` ASC) 
, ADD UNIQUE INDEX `companyname_UNIQUE` (`companyname` ASC) , RENAME TO  `companyinformation`.`companyinformation` ;
