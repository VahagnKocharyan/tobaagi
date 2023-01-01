-- MySQL dump 10.13  Distrib 8.0.27, for Linux (x86_64)
--
-- Host: localhost    Database: polytest
-- ------------------------------------------------------
-- Server version	8.0.27-0ubuntu0.20.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `LANGUAGE`
--

DROP TABLE IF EXISTS `LANGUAGE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `LANGUAGE` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'unique identifier ',
  `Rcode` varchar(256) NOT NULL COMMENT 'R code: Google language code for Speech Recognition',
  `Tcode` varchar(256) NOT NULL COMMENT 'T code: Google language code for Translation API',
  `Scode` varchar(256) NOT NULL COMMENT 'S code: Google language code for Speech Synthesis',
  `Language` varchar(256) NOT NULL COMMENT ' language',
  `Dialect` varchar(256) NOT NULL COMMENT 'country of language',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb3 COMMENT='poly LANGUAGE database';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `LANGUAGE`
--

LOCK TABLES `LANGUAGE` WRITE;
/*!40000 ALTER TABLE `LANGUAGE` DISABLE KEYS */;
INSERT INTO `LANGUAGE` VALUES (1,'en-US','en','en-US-Wavenet-C','English','United States'),(2,'fr-FR','fr','fr-FR-Wavenet-A','French',''),(3,'es-ES','es','es-ES-Wavenet-D','Spanish',''),(4,'en-GB','en','en-GB-Wavenet-C','English','United Kingdom'),(5,'en-IN','en','en-IN-Wavenet-C','English','India'),(6,'ja-JP','ja','ja-JP-Wavenet-A','Japanese',''),(7,'ar-EG','ar','ar-XA-Wavenet-A','Arabic',''),(8,'th-TH','th','th-TH-Standard-A','Thai',''),(9,'de-DE','de','de-DE-Wavenet-A','German',''),(10,'it-IT','it','it-IT-Wavenet-A','Italian',''),(11,'nl-NL','nl','nl-NL-Wavenet-A','Dutch',''),(12,'hi-IN','hi','hi-IN-Wavenet-A','Hindi','');
/*!40000 ALTER TABLE `LANGUAGE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PROMPT`
--

DROP TABLE IF EXISTS `PROMPT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PROMPT` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'unique identifier ',
  `PROMPTNAME` varchar(256) NOT NULL COMMENT 'Prompt type name',
  `PROMPTTEXT` varchar(256) NOT NULL COMMENT 'Prompt text',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb3 COMMENT='poly PROMPT database';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PROMPT`
--

LOCK TABLES `PROMPT` WRITE;
/*!40000 ALTER TABLE `PROMPT` DISABLE KEYS */;
INSERT INTO `PROMPT` VALUES (1,'Unrecognized','This is Poly. Phone number not recognized. Please register'),(2,'Selectlanguage','This is Poly Interpreter. Please select 1 to 5 for choosing translation language'),(3,'Confirmselection','To confirm – enter same number again. To change – enter a different number'),(4,'Wrongselection ','Please press a number between 1 and 5'),(5,'Starttalking  ','You may speak now');
/*!40000 ALTER TABLE `PROMPT` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UNIMRCPTIMEOUTS`
--

DROP TABLE IF EXISTS `UNIMRCPTIMEOUTS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `UNIMRCPTIMEOUTS` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'unique identifier of caller',
  `SINGLE_UTTERANCE` varchar(24) NOT NULL COMMENT 'By default, if the configuration parameter single-utterance is set to true, recognition is performed in the single utterance mode and is terminated upon an expiration of the speech complete timeout or an END-OF-SINGLE-UTTERANCE response delivered from the Google Cloud Speech service.',
  `SPEECH_COMPLETE_TIMEOUT` int NOT NULL COMMENT 'Specifies how long to wait in transition mode before triggering an end of speech input event. The complete timeout is used when there is an interim result available.',
  `SPEECH_INCOMPLETE_TIMEOUT` int NOT NULL COMMENT 'Specifies how long to wait in transition mode before triggering an end of speech input event. The incomplete timeout is used as long as there is no interim result available. Afterwards, the complete timeout is used.',
  `NOINPUT_TIMEOUT` int NOT NULL COMMENT 'Specifies how long to wait before triggering a no-input event.',
  `INPUT_TIMEOUT` int NOT NULL COMMENT 'Specifies how long to wait for input to complete.',
  `DTMF_INTERDIGIT_TIMEOUT` int NOT NULL COMMENT 'Specifies a DTMF inter-digit timeout.',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3 COMMENT='poly UNIMRCP TIMEOUTS table';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UNIMRCPTIMEOUTS`
--

LOCK TABLES `UNIMRCPTIMEOUTS` WRITE;
/*!40000 ALTER TABLE `UNIMRCPTIMEOUTS` DISABLE KEYS */;
INSERT INTO `UNIMRCPTIMEOUTS` VALUES (1,'false',1500,15000,10000,30000,1000);
/*!40000 ALTER TABLE `UNIMRCPTIMEOUTS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER`
--

DROP TABLE IF EXISTS `USER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'unique identifier of caller',
  `Name` varchar(256) NOT NULL COMMENT 'user name',
  `CLI` varchar(256) NOT NULL COMMENT 'user callerid',
  `SERVER` varchar(256) NOT NULL COMMENT 'server location',
  `R0` varchar(256) NOT NULL COMMENT 'primary user language',
  `R1` varchar(256) NOT NULL COMMENT 'guest user language 1',
  `R2` varchar(256) NOT NULL COMMENT 'guest user language 2',
  `R3` varchar(256) NOT NULL COMMENT 'guest user language 3',
  `R4` varchar(256) NOT NULL COMMENT 'guest user language 4',
  `R5` varchar(256) NOT NULL COMMENT 'guest user language 5',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb3 COMMENT='poly user database';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER`
--

LOCK TABLES `USER` WRITE;
/*!40000 ALTER TABLE `USER` DISABLE KEYS */;
INSERT INTO `USER` VALUES (1,'Test IL','101','USA','en-US','es-ES','ja-JP','nl-NL','fr-FR','it-IT'),(2,'Test IL','102','USA','fr-FR','es-ES','ja-JP','nl-NL','en-US','it-IT'),(7,'Itay','972526205576','USA','es-ES','en-US','ja-JP','nl-NL','fr-FR','it-IT'),(8,'Ike','972544453213','USA','en-US','es-ES','ja-JP','nl-NL','fr-FR','ar-EG'),(9,'Test IL','37498000662','USA','en-US','es-ES','ja-JP','nl-NL','fr-FR','it-IT'),(10,'Test IL','01137498000662','USA','en-US','es-ES','ja-JP','nl-NL','fr-FR','it-IT');
/*!40000 ALTER TABLE `USER` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-01-10 16:46:29
