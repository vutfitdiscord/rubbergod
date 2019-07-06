-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               10.1.26-MariaDB-0+deb9u1 - Debian 9.1
-- Server OS:                    debian-linux-gnu
-- HeidiSQL Version:             9.5.0.5196
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- Dumping database structure for rubbergod
CREATE DATABASE IF NOT EXISTS `rubbergod` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;
USE `rubbergod`;

-- Dumping structure for table rubbergod.bot_karma
CREATE TABLE IF NOT EXISTS `bot_karma` (
  `member_id` varchar(30) NOT NULL DEFAULT 'a',
  `karma` int(11) DEFAULT NULL,
  `nick` text,
  PRIMARY KEY (`member_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping data for table rubbergod.bot_karma: ~0 rows (approximately)
/*!40000 ALTER TABLE `bot_karma` DISABLE KEYS */;
/*!40000 ALTER TABLE `bot_karma` ENABLE KEYS */;

-- Dumping structure for table rubbergod.bot_karma_emoji
CREATE TABLE IF NOT EXISTS `bot_karma_emoji` (
  `emoji_id` varchar(50) UNIQUE,
  `value` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping data for table rubbergod.bot_karma_emoji: ~0 rows (approximately)
/*!40000 ALTER TABLE `bot_karma_emoji` DISABLE KEYS */;
/*!40000 ALTER TABLE `bot_karma_emoji` ENABLE KEYS */;

-- Dumping structure for table rubbergod.bot_permit
CREATE TABLE IF NOT EXISTS `bot_permit` (
  `login` varchar(64) UNIQUE,
  `discord_name` text,
  `discord_id` text,
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping data for table rubbergod.bot_permit: ~0 rows (approximately)
/*!40000 ALTER TABLE `bot_permit` DISABLE KEYS */;
/*!40000 ALTER TABLE `bot_permit` ENABLE KEYS */;

-- Dumping structure for table rubbergod.bot_valid_persons
CREATE TABLE IF NOT EXISTS `bot_valid_persons` (
  `login` varchar(64) UNIQUE,
  `name` text,
  `year` text,
  `code` text DEFAULT NULL,
  `status` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `bot_reminders` (
  `reminderID` int NOT NULL AUTO_INCREMENT,
  `message` text DEFAULT NULL,
  `channelID` varchar(64) DEFAULT NULL,
  `remind_time` timedate DEFAULT NULL,
  PRIMARY KEY (`reminderID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `bot_people_to_remind` (
  `userID` varchar(50) NOT NULL,
  `reminderID` int NOT NULL,
  `private` BOOLEAN,
  FOREIGN KEY (`reminderID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping data for table rubbergod.bot_valid_persons: ~0 rows (approximately)
/*!40000 ALTER TABLE `bot_valid_persons` DISABLE KEYS */;
/*!40000 ALTER TABLE `bot_valid_persons` ENABLE KEYS */;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
