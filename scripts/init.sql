CREATE DATABASE mylib;

USE mylib;

CREATE TABLE `resource` (
  `id` varchar(40) NOT NULL,
  `name` varchar(255) NOT NULL,
  `summary` text,
  `type` enum('txt','pdf','word','excel') DEFAULT 'txt',
  `created_time` int(11) DEFAULT NULL,
  `updated_time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;