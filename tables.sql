SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

DROP DATABASE IF EXISTS `Users`;
CREATE DATABASE `Users` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci */;
USE `Users`;

DELIMITER ;;

DROP PROCEDURE IF EXISTS `get_object`;;
CREATE PROCEDURE `get_object`(IN table_name VARCHAR(64), IN id INT)
BEGIN
  SET @query = CONCAT('SELECT * FROM ', table_name, ' WHERE id=', id, ' LIMIT 1');
  PREPARE stmt FROM @query;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;
END;;

DROP PROCEDURE IF EXISTS `select_objects`;;
CREATE PROCEDURE `select_objects`(IN `table_name` varchar(64), IN `offset_num` INT, IN `limit_num` INT)
BEGIN
  SET @query = CONCAT('SELECT * FROM ',table_name,' LIMIT ', limit_num, ', ', offset_num);
  PREPARE stmt FROM @query;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;

  SET @query = CONCAT('SELECT COUNT(*) from ',table_name);
  PREPARE stmt FROM @query;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;
END;;

DROP PROCEDURE IF EXISTS `select_users`;;
CREATE PROCEDURE `select_users`(IN table_name VARCHAR(64), IN offset_num INT, IN limit_num INT, IN search VARCHAR(64))
BEGIN
  SET @query = CONCAT('SELECT * FROM ',table_name);
  IF search IS NOT NULL THEN
    SET @query = CONCAT(@query, " WHERE name LIKE '%", search, "%'");
  END IF;
  IF limit_num IS NOT NULL THEN
    SET @query = CONCAT(@query, ' LIMIT ', limit_num);
  END IF;
  IF offset_num IS NOT NULL THEN
    SET @query = CONCAT(@query, ' OFFSET ', offset_num);
  END IF;
  PREPARE stmt FROM @query;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;

  SET @query = CONCAT('SELECT COUNT(*) FROM ',table_name);
  IF search IS NOT NULL THEN
    SET @query = CONCAT(@query, " WHERE name LIKE '%", search, "%'");
  END IF;
  PREPARE stmt FROM @query;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;
END;;

DROP PROCEDURE IF EXISTS `select_usercourses`;;
CREATE PROCEDURE `select_usercourses`(IN table_name VARCHAR(64), IN offset_num INT, IN limit_num INT, IN user_id INT)
BEGIN
  SET @query = CONCAT('SELECT * FROM ',table_name);
  IF user_id IS NOT NULL THEN
    SET @query = CONCAT(@query, ' WHERE user_id = ', user_id);
  END IF;
  IF limit_num IS NOT NULL THEN
    SET @query = CONCAT(@query, ' LIMIT ', limit_num);
  END IF;
  IF offset_num IS NOT NULL THEN
    SET @query = CONCAT(@query, ' OFFSET ', offset_num);
  END IF;

  PREPARE stmt FROM @query;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;
END;;

DROP PROCEDURE IF EXISTS `insert_object`;;
CREATE PROCEDURE `insert_object`(IN table_name VARCHAR(64), IN fields VARCHAR(256), IN insert_values VARCHAR(256))
BEGIN
  SET @query = CONCAT('INSERT INTO ', table_name, ' (', fields, ') VALUES(', insert_values, ')');
  PREPARE stmt FROM @query;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;
END;;

DROP PROCEDURE IF EXISTS `update_object`;;
CREATE PROCEDURE `update_object`(IN table_name VARCHAR(64), IN update_values VARCHAR(256), IN id INT)
BEGIN
  SET @query = CONCAT('UPDATE ', table_name, ' SET ', update_values, ' WHERE id=', id);
  PREPARE stmt FROM @query;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;
END;;

DROP PROCEDURE IF EXISTS `delete_objects`;;
CREATE PROCEDURE `delete_objects`(IN table_name VARCHAR(64), IN field VARCHAR(64), IN value VARCHAR(64))
BEGIN
  SET @query = CONCAT('DELETE FROM ', table_name, ' WHERE ', field, '=', value);
  PREPARE stmt FROM @query;
  EXECUTE stmt;
  DEALLOCATE PREPARE stmt;
END;;

DELIMITER ;

DROP TABLE IF EXISTS `course`;
CREATE TABLE `course` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(8) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_code` (`code`),
  KEY `course_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

INSERT INTO `course` (`id`, `code`, `name`) VALUES
(1,	'P012345',	'Python-Base'),
(2,	'P234567',	'Python-Database'),
(3,	'H345678',	'HTML'),
(4,	'J456789',	'Java-Base'),
(5,	'JS543210',	'JavaScript-Base');

DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `phone` varchar(13) COLLATE utf8_unicode_ci DEFAULT NULL,
  `mobile` varchar(13) COLLATE utf8_unicode_ci DEFAULT NULL,
  `status` varchar(1) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_name` (`name`),
  KEY `user_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `usercourse`;
CREATE TABLE `usercourse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `usercourse_user_id` (`user_id`),
  KEY `usercourse_course_id` (`course_id`),
  CONSTRAINT `usercourse_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `usercourse_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `course` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
